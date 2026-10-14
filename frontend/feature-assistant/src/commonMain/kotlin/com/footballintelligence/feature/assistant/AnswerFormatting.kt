package com.footballintelligence.feature.assistant

import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle

private val LIST_MARKER = Regex("""^\s*[*-]\s+""")
private const val BOLD = "**"
private const val BULLET = "•  "

/**
 * The assistant's answer with the little markdown models use made readable:
 * `**bold**` becomes bold text and `*` or `-` list markers become bullets.
 * Anything else, including an unmatched `**`, is shown as written.
 */
fun formatAnswer(text: String): AnnotatedString = buildAnnotatedString {
    text.lines().forEachIndexed { index, line ->
        if (index > 0) append('\n')
        val bulleted = LIST_MARKER.find(line)?.let { BULLET + line.substring(it.range.last + 1) } ?: line
        appendWithBold(bulleted)
    }
}

private fun AnnotatedString.Builder.appendWithBold(line: String) {
    var rest = line
    while (true) {
        val open = rest.indexOf(BOLD)
        val close = if (open < 0) -1 else rest.indexOf(BOLD, open + BOLD.length)
        if (close < 0) {
            append(rest)
            return
        }
        append(rest.substring(0, open))
        withStyle(SpanStyle(fontWeight = FontWeight.Bold)) {
            append(rest.substring(open + BOLD.length, close))
        }
        rest = rest.substring(close + BOLD.length)
    }
}

/**
 * The confidence to show under an answer, or null to show none. The server's
 * confidence measures how well retrieved documents matched, so an answer from
 * tools alone, with no sources, would always read 0%.
 */
fun retrievalConfidence(confidence: Double, sourceCount: Int): Double? =
    confidence.takeIf { sourceCount > 0 }
