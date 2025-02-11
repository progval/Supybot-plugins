# Trivia

Simple trivia plugin for Limnoria, which asks a channel questions, gives hints,
and awards points for good answer.

Questions and answers should be in the file `questions.txt` (path is configurable
as `supybot.plugins.Trivia.questionFile`.

The format of this file is: on each line, write a question, followed by the `*`
separator, followed by the answer. The separator is configurable as
`supybot.plugins.Trivia.questionFileSeparator`.
