# ruyijs-trial

在 GitHub Actions 的 Windows runner 上试用 [ruyiJS](https://github.com/martinkeith700/ruyiJS)（该库仅提供 Windows x64 wheel，本仓库用于在云端验证其真实表现）。

## 怎么跑

```sh
gh workflow run smoke.yml          # 或在 GitHub 网页 Actions 页签点 Run workflow
gh run watch                       # 观察进度
gh run view --log | grep -E "PASS|FAIL|ALL GREEN"
```

`smoke_test.py` 只做无害验证：引擎 eval、Python↔JS 桥、指纹配置、确定性时钟、JSError、真实网络栈访问 example.com。不包含任何对风控目标站点的绕过测试。

## 加自己的脚本

把脚本放进本仓库，然后在 `smoke.yml` 里加一步 `python your_script.py` 即可。

## 清理

试用完删仓库：GitHub 网页 → Settings → Danger Zone → Delete this repository。
