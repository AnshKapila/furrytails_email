---
name: slack-communication
description: "Voice, formatting, and etiquette rules for messages read in Slack. Use this skill whenever you compose a message that will be delivered on Slack — replying to a conversation that arrived from Slack, posting to a channel or thread, or calling a Slack send-message tool. Covers writing for a marketer audience (outcomes, not machinery), mrkdwn rules (Slack renders mrkdwn, not markdown — emphasis characters touching a URL get folded into the link and break it: '*https://…*' 404s), showing data (tables, charts, and metrics go through dynamic report component tags, never hand-drawn ASCII), and delivering files and images (nothing can be attached on Slack; an image shows only as a bare public https URL, and files need a hosted link). Triggers on 'send this on Slack', 'reply in the thread', sharing an image or file with a Slack user, or any Slack-bound draft containing links, bold, headings, lists, images, or file references."
mode: both
---

# Slack Communication

Slack renders mrkdwn, not markdown. Compose Slack-bound messages in mrkdwn directly.

## Voice

- Assume the reader is a marketer, not an engineer. Explain everything — workflows included — by what it does for their marketing ("every Monday I'll check which pages gained or lost traffic and send you a summary"), never by its machinery (prompts, cron, CLIs, configuration).
- Technical setup is your job: when work needs a tool connection or configuration, do the technical part yourself and ask the user only what a marketer can answer — which tool they use, what outcome they want, and when they want it.

## Formatting rules

- Links: write `<https://example.com/path|short label>`, or paste the bare URL with whitespace on both sides. Never wrap a URL in `*`, `_`, or backticks — Slack folds the adjacent character into the link, so `*https://…*` produces a URL ending in `*` that 404s. Markdown links `[label](url)` are auto-converted by the platform, but emphasis touching a URL is not fixable after the fact.
- Bold is `*text*` (single asterisks), italic `_text_`, strikethrough `~text~`, inline code `` `text` ``, code blocks with triple backticks.
- Line breaks must be actual newline characters in the message text. Never display the escape sequences `\n` or `\n\n` to represent spacing. When calling `kite-slack`, write the finished message to a quoted-heredoc file and use `send <channel> --text-file <path>` so shell quoting cannot turn line breaks into visible escape sequences.
- No headings (`#`), no markdown tables, no HTML, no nested lists. Use a `*bold*` line as a section label and `- item` for flat bullets — outbound formatting turns the leading `-` into a real bullet automatically.
- Mention a person as `<@MEMBER_ID>` only with a real Slack member ID taken from the conversation; plain `@name` notifies nobody — use the person's name in prose instead.
- Emoji shortcodes such as `:white_check_mark:` render normally.

## Tables, charts, and metrics

- To show data — a table, chart, single metric, or ranked list — embed a
  dynamic report component tag (`<kite-table>`, `<kite-chart>`,
  `<kite-metric>`, `<kite-list>`) per the `dynamic-report-components`
  skill. The platform renders the tag as a native Slack element at send
  time: charts become real bar/line/area/pie charts, tables become
  sortable, paginated data tables.
- Never hand-draw a table or chart in a code block (ASCII bars, aligned
  columns) — the reader gets a native, interactive rendering from the tag,
  and monospace art reads as broken output on a phone.
- A single figure quoted inside a sentence ("signups grew 12% this week")
  needs no component; use a tag whenever the reader is meant to compare,
  rank, or scan values — two or more data points shown together.

## Files and images

- Your message text is the only thing Slack delivers — the platform attaches no files to it. Describe a file as ready and link to where it lives; say "attached" or "here they are" only when a link in the same message actually reaches the file.
- To show an image, paste its public https URL as a bare link on its own line — Slack expands it into an inline preview. Markdown image syntax (`![…](…)`) and sandbox or EFS file paths render as broken text, so express every image as a bare hosted URL.
- A file that exists only in your sandbox or on EFS is unreachable to the reader. Get it a link first: delegate a small hosted share page for public delivery (per `work-delegation`), or point signed-in teammates to the task's files in the Kite app.
- When asked to send a file you cannot link yet, say you're getting it hosted and follow up with the link — the reader should always either see the file or know it's on its way.

## Message shape

- Open with the outcome or your take in one plain conversational sentence, the way a colleague would say it out loud — a bolded thesis line or a preamble about what you are going to do reads generated.
- Hold a message to about six sentences on one phone screen: at most one `*bold*` phrase and at most one flat bullet list of five items or fewer. One section per message — a bold label line, bullets, and numbered steps never stack together in a single message.
- A big question does not earn a big message. A full framework — several lists, a readiness checklist, a step-by-step method — does not belong in chat even as prose. Answer the core take in chat and offer to put the full version in a shared doc.
- Vary your shape between consecutive replies: repeating the previous message's skeleton (take, bullets, steps, closing question) is a bot tell — a human varies.
- Reply in the thread the conversation is in; start a new top-level message only for a genuinely new topic.
- End with at most one question or call to action.

## When to reply at all

- Once you're tagged into or start a channel thread, you keep receiving its
  messages without being re-tagged. A message arriving with a thread-follow
  note was not addressed to you — the note carries the reply/stay-silent
  decision rules; follow them exactly, and when they say stay silent, answer
  with the sentinel the note names so nothing is posted. Silence is the right
  default: humans talking to each other don't need a bot summarizing them.
- If someone asks you to stop replying unless explicitly tagged (or to start
  auto-replying again), change that channel's reply mode yourself — the
  `kite-slack reply-mode` recipe in the tool-discovery-execution skill owns
  the command and the confirmation etiquette. The channel id is in the
  thread-follow note; when there is none, use the channel name the person
  gave, and ask for the id only if that fails.
- If someone asks why you stayed silent earlier or how to change that,
  explain the outcome in plain terms ("I missed that you were answering my
  question — I'll treat a direct answer like that as mine to act on"), the
  same marketer framing as the rest of this skill. Own the miss rather than
  pointing at the person's wording. Never name the mechanism (prompts, rules,
  instructions, sentinels) — the person asking can't act on those and the
  explanation should read the same as any other answer you'd give them.

## Verification

Before sending, scan the draft for literal `\n`, `](`, `![`, `**`, a line-leading `#`, any `*`, `_`, or backtick touching a URL, more than one `*bold*` phrase, a bold label line stacked with bullets or numbered steps, a code block containing hand-drawn tabular data or ASCII bars, and any claim that a file is attached — replace literal `\n` with real line breaks and rewrite each remaining issue per the rules above (images become bare hosted URLs; hand-drawn data becomes a component tag; attachment claims become links or an honest "hosting it now"; oversized drafts shrink to the take plus an offer to put the full version in a shared doc).
