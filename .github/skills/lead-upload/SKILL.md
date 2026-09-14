---
name: lead-upload
description: Turn an event's attendee list into a CRM upload request. Use when someone comments /lead-upload on an event issue, or asks to hand leads over to marketing ops.
---

# Lead upload

把一场结束的活动的参会名单，整理成营销运营团队做 CRM 导入时要的格式。

## 开始之前

1. 从 Issue 正文里读出 `platform_event_id` 和活动代号。两者缺一就停下来回帖说明，不要猜。
2. 确认 Issue 带着 `event-done` 标签。没有就停下来问。
3. 读一眼仓库根目录的 `AGENTS.md`，命名规则以那份为准。

## 步骤

1. 运行 `python3 -m scripts.export_attendees --event-id <id> --out leads.csv`。
2. 检查产出的 CSV，列必须正好是这几个，顺序也要一致。
   `email, first_name, last_name, company, job_title, country, campaign, consent`
3. `consent` 列为空的行整行删掉，并在最后的回帖里报告删了多少行。
4. `campaign` 列全部填 Issue 里的活动代号，逐字复制，不要重新拼。
5. `country` 用两位国家码。活动平台给的是地区名的，按 `config/country-map.json` 转换。
6. 在 YOUR-ORG/crm-requests 仓库开一个 Issue，标题 `CRM upload: <活动代号>`，
   正文用 `templates/crm-request.md`，把 leads.csv 作为附件评论上去。
7. 回到活动 Issue 回帖，写清楚导出了多少行、删了多少行、需求单的链接。
8. 把标签从 `event-done` 换成 `leads-submitted`。

## 注意

- `DRY_RUN` 为 true 时，第 6 步和第 8 步不要执行，把准备发出的内容打印出来即可。
- 任何一行数据看起来异常（邮箱格式不对、公司名为空），不要自己修，列出来交给人判断。
- 名单里的邮箱地址不要写进回帖、日志或者提交信息里。
