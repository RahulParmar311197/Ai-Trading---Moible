package com.aitrading.app

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** Advisory-only AI client. It never exposes broker credentials or executes orders. */
class AiApiClient(private val baseUrl: String) {
    fun analyze(symbol: String, timeframe: String): String {
        require(baseUrl.isNotBlank()) { "AI API base URL is not configured" }
        require(symbol.isNotBlank()) { "symbol is required" }

        val endpoint = URL(baseUrl.trimEnd('/') + "/api/v1/ai/analyze")
        val connection = endpoint.openConnection() as HttpURLConnection
        connection.requestMethod = "POST"
        connection.connectTimeout = 10_000
        connection.readTimeout = 20_000
        connection.setRequestProperty("Content-Type", "application/json")
        connection.doOutput = true

        val request = JSONObject()
            .put("symbol", symbol.trim())
            .put("timeframe", timeframe)
            .put("market_context", JSONObject())
            .put("smc_context", JSONObject())
            .put("ict_context", JSONObject())
            .put("technical_context", JSONObject())
            .put("options_context", JSONObject())
            .put("risk_context", JSONObject())
            .put("strategy_context", JSONObject())

        return try {
            connection.outputStream.use { it.write(request.toString().toByteArray(Charsets.UTF_8)) }
            val status = connection.responseCode
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val body = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
            if (status !in 200..299) {
                throw IllegalStateException("AI service request failed (HTTP $status)")
            }
            JSONObject(body).optString("summary").ifBlank {
                throw IllegalStateException("AI service returned no summary")
            }
        } finally {
            connection.disconnect()
        }
    }
}
