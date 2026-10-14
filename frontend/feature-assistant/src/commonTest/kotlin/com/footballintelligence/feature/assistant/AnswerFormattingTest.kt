package com.footballintelligence.feature.assistant

import androidx.compose.ui.text.font.FontWeight
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class AnswerFormattingTest {
    @Test
    fun `bold markers are removed and the text between them is bold`() {
        val formatted = formatAnswer("The **Everton win** chance is 43%.")
        assertEquals("The Everton win chance is 43%.", formatted.text)
        val bold = formatted.spanStyles.single()
        assertEquals(FontWeight.Bold, bold.item.fontWeight)
        assertEquals("Everton win", formatted.text.substring(bold.start, bold.end))
    }

    @Test
    fun `list markers become bullets`() {
        val formatted = formatAnswer("Probabilities:\n*   **Draw:** 25.2%\n- Away: 31.8%")
        assertEquals("Probabilities:\n•  Draw: 25.2%\n•  Away: 31.8%", formatted.text)
    }

    @Test
    fun `an unmatched bold marker is left as written`() {
        assertEquals("2 ** 3", formatAnswer("2 ** 3").text)
        assertTrue(formatAnswer("2 ** 3").spanStyles.isEmpty())
    }

    @Test
    fun `citation markers are hidden from the reader`() {
        val answer = "Everton are favourites [source: tool predict_match]. " +
            "Form is mixed [source: team_matches]."
        assertEquals("Everton are favourites. Form is mixed.", formatAnswer(answer).text)
    }

    @Test
    fun `plain text is unchanged`() {
        val text = "I don't have enough information in my knowledge base to answer that."
        assertEquals(text, formatAnswer(text).text)
    }

    @Test
    fun `confidence is shown only for answers drawn from sources`() {
        assertNull(retrievalConfidence(confidence = 0.0, sourceCount = 0))
        assertEquals(0.84, retrievalConfidence(confidence = 0.84, sourceCount = 2))
    }
}
