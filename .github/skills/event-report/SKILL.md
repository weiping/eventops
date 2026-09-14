---
name: event-report
description: Write the post-event report back onto the event issue. Use when someone comments /event-report on an event issue, or asks for attendance and survey results to be summarised.
---

# Event report

把一场结束的活动的出席数据和问卷结果，整理成复盘报告，贴回这场活动的 Issue。

## 开始之前

1. 从 Issue 正文里读出 `platform_event_id` 和活动代号。两者缺一就停下来回帖说明，不要猜。
2. 确认 Issue 带着 `event-done` 标签。没有就停下来问。

## 步骤

1. 运行 `python3 -m scripts.export_attendance --event-id <id> --out attendance.json`。
2. 报告分四段，顺序固定。
   报名与实际出席人数及出席率、受众构成、问卷结果要点、下一次该改什么。
3. 出席率拿实际出席除以报名数，保留一位小数。
4. 受众构成按公司域名归类，只报分布，不列公司名，更不列个人。
5. 问卷自由填写题最多摘三条，摘的时候去掉可以指向具体某个人的信息。
6. 把报告作为评论贴回活动 Issue。

## 注意

- `DRY_RUN` 为 true 时，第 6 步不要执行，把报告打印出来即可。
- 出席人数低于报名数一半时，在报告里单独标出来，不要一句带过。
- 报告里不要出现任何参会者的姓名或邮箱。
