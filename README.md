# eventops

把办活动的手工流程搬进 GitHub 仓库的一份可运行实现。一张 Issue 表单、一个标签、一条
Actions 工作流，一场活动就自己就位，每天早上自己筛报名，结束之后自己收尾。

配套文章讲了每一处为什么这么设计。这里只讲怎么跑起来。

## 它由什么构成

| 路径 | 作用 |
| --- | --- |
| `.github/ISSUE_TEMPLATE/webinar.yml` | 输入契约，一场活动的全部参数从这张表单进来 |
| `.github/workflows/hello-event.yml` | 最小回环，贴标签然后回帖告诉你活动代号 |
| `.github/workflows/event-setup.yml` | 建场，复制落地页、生成链接、开需求单、加看板 |
| `.github/workflows/daily-screening.yml` | 每天早上筛报名，推进标签，失败时大声喊 |
| `.github/workflows/slash-commands.yml` | `/lead-upload` 和 `/event-report` 两个斜杠命令 |
| `.github/workflows/tests.yml` | 每个 PR 跑测试、lint 和契约检查 |
| `.github/skills/` | 交给 Copilot 执行的操作手册 |
| `AGENTS.md` | 团队共享的命名、时区和文风规则 |
| `scripts/` | 解析、校验、链接生成、编排、筛查 |

## 本地跑起来

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python3 -m pytest -q
```

42 条测试，不需要网络，不需要任何密钥。

想看主流程的产出，用彩排模式跑一次建场。

```bash
export EVENT=$(python3 - <<'PY'
import json
from scripts.event_form import parse_event
print(json.dumps(parse_event(open("tests/fixtures/webinar-issue.md").read()).to_dict(), ensure_ascii=False))
PY
)
DRY_RUN=true EVENT_PLATFORM_URL=https://api.example.com \
  EVENT_PLATFORM_TOKEN=x python3 -m scripts.setup_event
```

它会在 `drafts/` 下生成邀请邮件草稿、需求单和链接表，同时把要发给活动平台的请求打进日志，
一个字节都不会发出去。

## 上生产之前要配的东西

仓库变量（Settings 里的 Variables）。

| 名字 | 说明 |
| --- | --- |
| `DRY_RUN` | 建议先设成 `true`，信得过了再改 `false`。不设也按 `true` 处理 |
| `EVENT_PLATFORM_URL` | 活动平台 API 的根地址 |
| `OPS_ONCALL` | 定时任务失败时把告警 Issue 指派给谁 |

仓库密钥（Secrets）。

| 名字 | 说明 |
| --- | --- |
| `EVENT_PLATFORM_TOKEN` | 活动平台的 API token |
| `OPS_TOKEN` | 细粒度 PAT，跨仓库开 Issue 和加项目看板要用 |
| `COPILOT_TOKEN` | 细粒度 PAT，需要 Copilot Requests 权限，经典 PAT 不支持 |
| `SLACK_WEBHOOK` | 告警推送地址 |

另外把 `CODEOWNERS`、`.github/skills/lead-upload/SKILL.md` 和工作流里的
`YOUR-ORG`、`YOUR-HANDLE` 换成你自己的。

## 需要你自己接上去的部分

`scripts/platform_client.py` 里的接口路径按一个通用的 REST 形状写的，换成你自己活动平台的
真实路径即可，DRY_RUN 闸门在 `_request` 这一层，换路径不影响它。

`scripts/screen_registrants.py` 里的 `crm` 命令是个占位，换成你自己 CRM 的命令行工具。

`scripts/export_attendees.py` 和 `scripts/export_attendance.py` 两个导出脚本没有包含在内，
它们完全取决于你的平台返回什么，跟仓库里其他脚本同构。

## 安全

仓库里不放任何真实密钥。上手第一天就把 Settings 里的 secret scanning 和 push protection 打开。

工作流里所有外部可控的字符串，包括 Issue 正文和评论正文，一律走 `env` 注入，不进
`${{ }}` 插值位置。改工作流的时候请守住这条。
