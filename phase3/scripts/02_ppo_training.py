#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 / 任务3.2: PPO 强化学习智能体训练(序贯检测策略)

环境(向量化, B 个并行 episode):
  状态  s = [x*mask, mask]  (2m 维)
  动作  a ∈ {0..m-1: 测第j项} ∪ {m: 停止并判定}  (已测项被屏蔽)
  奖励  测第j项: -lambda*cost[j];  停止: +1 判对 / -1 判错(用掩码分类器)
PPO: 共享 trunk 的 actor-critic, GAE, clip 目标, 熵正则。从零实现(不依赖 gym/SB3)。

产出: outputs/models/ppo_agent.pt, outputs/figures/ppo_training.png
"""
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import _common as C

torch.manual_seed(0); np.random.seed(0)
NEG = -1e9


class ActorCritic(nn.Module):
    def __init__(self, m, hid=128):
        super().__init__()
        self.trunk = nn.Sequential(nn.Linear(2 * m, hid), nn.Tanh(), nn.Linear(hid, hid), nn.Tanh())
        self.actor = nn.Linear(hid, m + 1)
        self.critic = nn.Linear(hid, 1)

    def forward(self, s):
        h = self.trunk(s)
        return self.actor(h), self.critic(h).squeeze(-1)


class VecEnv:
    """B 个并行序贯检测环境。"""
    def __init__(self, Xs, y, idx, clf, lam, rng, B=64, class_w=9.0):
        self.X, self.y, self.idx = Xs, y, idx
        self.clf = clf; self.lam = lam; self.rng = rng; self.B = B
        self.m = Xs.shape[1]
        self.class_w = class_w   # 失效类奖励权重(抵消不平衡, 使"全判正常"得不到便宜)
        self.cost = torch.tensor(C.COST)
        self.reset_all()

    def reset_all(self):
        self.chip = self.rng.choice(self.idx, size=self.B)
        self.mask = np.zeros((self.B, self.m), dtype=np.float32)

    def _reset(self, i):
        self.chip[i] = self.rng.choice(self.idx)
        self.mask[i] = 0.0

    def state(self):
        x = self.X[self.chip]
        return torch.tensor(np.concatenate([x * self.mask, self.mask], axis=1))

    def action_mask(self):
        # 已测的 acquire 动作不可选; stop 永远可选; 全测后只能 stop
        am = np.concatenate([1 - self.mask, np.ones((self.B, 1), np.float32)], axis=1)
        return torch.tensor(am)

    def step(self, actions):
        actions = actions.numpy()
        rew = np.zeros(self.B, np.float32); done = np.zeros(self.B, np.float32)
        info_correct = np.full(self.B, -1); info_ncost = np.zeros(self.B, np.float32)
        info_y = np.full(self.B, -1)
        stop = actions == self.m
        acq = ~stop
        # acquire
        ai = np.where(acq)[0]
        for i in ai:
            j = actions[i]
            self.mask[i, j] = 1.0
            rew[i] = -self.lam * float(C.COST[j])
        # stop -> classify
        si = np.where(stop)[0]
        if len(si):
            x = torch.tensor(self.X[self.chip[si]])
            mk = torch.tensor(self.mask[si])
            with torch.no_grad():
                pred = self.clf(x, mk).argmax(1).numpy()
            yt = self.y[self.chip[si]]
            correct = (pred == yt).astype(np.float32)
            weight = np.where(yt == 1, self.class_w, 1.0).astype(np.float32)
            rew[si] += weight * (2 * correct - 1)   # 失效判对/判错权重更大
            done[si] = 1.0
            for k, i in enumerate(si):
                info_correct[i] = int(correct[k]); info_ncost[i] = float((self.mask[i] * C.COST).sum())
                info_y[i] = int(yt[k])
        # 强制: 全测仍未停 -> 下步只能 stop(由 action_mask 保证); 这里不额外处理
        for i in si:
            self._reset(i)
        return rew, done, info_correct, info_ncost, info_y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lam', type=float, default=0.02, help='时间成本权重')
    ap.add_argument('--class_w', type=float, default=6.0, help='失效类奖励权重(<=0 则用 类别比)')
    ap.add_argument('--updates', type=int, default=400)
    ap.add_argument('--B', type=int, default=64)
    ap.add_argument('--T', type=int, default=32)
    args = ap.parse_args()

    print("=" * 60); print(f"Phase 3 / 3.2  PPO 训练 (lambda={args.lam})"); print("=" * 60)
    Xs, y, train_idx, test_idx = C.load()
    m = Xs.shape[1]
    clf = C.MaskedClassifier(m); clf.load_state_dict(torch.load(C.out('models', 'masked_classifier.pt'))); clf.eval()
    rng = np.random.default_rng(0)
    class_w = args.class_w if args.class_w > 0 else float((y[train_idx] == 0).sum() / max((y[train_idx] == 1).sum(), 1))
    print(f"class_w (failure reward weight) = {class_w:.1f}")
    env = VecEnv(Xs, y, train_idx, clf, args.lam, rng, B=args.B, class_w=class_w)
    net = ActorCritic(m); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    gamma, lam_gae, clip, ent_c, vf_c = 0.99, 0.95, 0.2, 0.01, 0.5

    hist = {'reward': [], 'acc': [], 'cost': []}
    for upd in range(args.updates):
        S, A, LP, R, V, D, M = [], [], [], [], [], [], []
        ep_correct, ep_cost, ep_y = [], [], []
        for t in range(args.T):
            s = env.state(); am = env.action_mask()
            logits, v = net(s)
            logits = logits + (am - 1) * 1e9  # 屏蔽非法动作
            dist = torch.distributions.Categorical(logits=logits)
            a = dist.sample()
            S.append(s); A.append(a); LP.append(dist.log_prob(a).detach()); V.append(v.detach()); M.append(am)
            rew, done, ic, nc, iy = env.step(a)
            R.append(torch.tensor(rew)); D.append(torch.tensor(done))
            for k in range(env.B):
                if done[k]:
                    ep_correct.append(ic[k]); ep_cost.append(nc[k]); ep_y.append(iy[k])
        # bootstrap value
        with torch.no_grad():
            _, last_v = net(env.state())
        # GAE
        S = torch.stack(S); A = torch.stack(A); LP = torch.stack(LP); V = torch.stack(V)
        R = torch.stack(R); D = torch.stack(D); M = torch.stack(M)
        adv = torch.zeros_like(R); gae = torch.zeros(env.B)
        for t in reversed(range(args.T)):
            nextv = last_v if t == args.T - 1 else V[t + 1]
            delta = R[t] + gamma * nextv * (1 - D[t]) - V[t]
            gae = delta + gamma * lam_gae * (1 - D[t]) * gae
            adv[t] = gae
        ret = adv + V
        # flatten
        bs = args.T * env.B
        S = S.reshape(bs, -1); A = A.reshape(bs); LP = LP.reshape(bs); M = M.reshape(bs, -1)
        adv = adv.reshape(bs); ret = ret.reshape(bs)
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        # PPO epochs
        for _ in range(4):
            idx = torch.randperm(bs)
            for st in range(0, bs, 512):
                b = idx[st:st + 512]
                logits, v = net(S[b]); logits = logits + (M[b] - 1) * 1e9
                dist = torch.distributions.Categorical(logits=logits)
                lp = dist.log_prob(A[b]); ratio = torch.exp(lp - LP[b])
                s1 = ratio * adv[b]; s2 = torch.clamp(ratio, 1 - clip, 1 + clip) * adv[b]
                pol = -torch.min(s1, s2).mean()
                vf = F.mse_loss(v, ret[b]); ent = dist.entropy().mean()
                loss = pol + vf_c * vf - ent_c * ent
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if ep_correct:
            corr = np.array(ep_correct); yy = np.array(ep_y)
            acc = float(corr.mean()); cost = float(np.mean(ep_cost))
            recall = float(corr[yy == 1].mean()) if (yy == 1).any() else 0.0
            hist['reward'].append(float(R.mean())); hist['acc'].append(acc); hist['cost'].append(cost)
            hist.setdefault('recall', []).append(recall)
            if (upd + 1) % 40 == 0:
                print(f"  upd {upd+1:3d}  ep_acc {acc:.3f}  recall {recall:.3f}  ep_cost {cost:5.1f}/{C.FULL_COST:.0f} "
                      f"({100*(1-cost/C.FULL_COST):.0f}% saved)")

    torch.save(net.state_dict(), C.out('models', 'ppo_agent.pt'))
    # 训练曲线
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        ax[0].plot(hist['acc']); ax[0].axhline(0.91, color='r', ls='--', label='target 0.91')
        ax[0].set_title('train episode accuracy'); ax[0].set_xlabel('update'); ax[0].legend(); ax[0].grid(alpha=.3)
        sv = [100 * (1 - c / C.FULL_COST) for c in hist['cost']]
        ax[1].plot(sv, color='C1'); ax[1].axhline(30, color='r', ls='--', label='target 30%')
        ax[1].set_title('test-time saved (%)'); ax[1].set_xlabel('update'); ax[1].legend(); ax[1].grid(alpha=.3)
        fig.tight_layout(); fig.savefig(C.out('figures', 'ppo_training.png'), dpi=150); plt.close()
    except Exception as e:
        print('plot skip:', e)
    print(f"\n✅ 已保存 ppo_agent.pt; 末期 ep_acc≈{np.mean(hist['acc'][-10:]):.3f}, "
          f"省时≈{100*(1-np.mean(hist['cost'][-10:])/C.FULL_COST):.0f}%")


if __name__ == '__main__':
    main()
