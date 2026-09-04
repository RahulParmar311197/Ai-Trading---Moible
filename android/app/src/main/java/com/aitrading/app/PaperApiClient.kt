package com.aitrading.app

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** Read-only paper portfolio client. It cannot access broker credentials or live execution. */
class PaperApiClient(private val baseUrl: String) {
    data class Account(val balance: String, val equity: String, val positions: Int, val tradingHalted: Boolean)

    fun account(): Account {
        val json = request("/api/v1/paper/account")
        return Account(
            balance = json.optString("balance", "0"),
            equity = json.optString("equity", "0"),
            positions = json.optInt("positions", 0),
            tradingHalted = json.optBoolean("trading_halted", true),
        )
    }

    private fun request(path: String): JSONObject {
        require(baseUrl.isNotBlank()) { "API base URL is not configured" }
        val connection = (URL(baseUrl.trimEnd('/') + path).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = 10_000
            readTimeout = 20_000
            setRequestProperty("Accept", "application/json")
        }
        return try {
            val status = connection.responseCode
            if (status !in 200..299) throw IllegalStateException("Paper service request failed (HTTP $status)")
            val body = connection.inputStream.bufferedReader().use { it.readText() }
            JSONObject(body)
        } finally {
            connection.disconnect()
        }
    }
}
