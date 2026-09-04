package com.aitrading.app

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class AuthApiClient(private val baseUrl: String) {
    data class User(val id: String, val email: String, val name: String, val status: String)
    data class LoginResult(val token: String, val user: User)

    fun login(email: String, password: String): LoginResult {
        val json = request("/api/v1/auth/login", "POST", JSONObject().apply {
            put("email", email)
            put("password", password)
        })
        return LoginResult(json.getString("access_token"), parseUser(json.getJSONObject("user")))
    }

    fun register(email: String, password: String, name: String): User =
        parseUser(request("/api/v1/auth/register", "POST", JSONObject().apply {
            put("email", email)
            put("password", password)
            put("name", name)
        }))

    fun me(token: String): User = parseUser(request("/api/v1/auth/me", "GET", null, token))

    fun logout(token: String) {
        request("/api/v1/auth/logout", "POST", null, token)
    }

    private fun parseUser(json: JSONObject): User = User(
        id = json.getString("id"),
        email = json.getString("email"),
        name = json.getString("name"),
        status = json.getString("status"),
    )

    private fun request(path: String, method: String, body: JSONObject?, token: String? = null): JSONObject {
        require(baseUrl.isNotBlank()) { "API base URL is not configured" }
        val connection = (URL(baseUrl.trimEnd('/') + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 10_000
            readTimeout = 20_000
            setRequestProperty("Accept", "application/json")
            if (body != null) {
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
            if (!token.isNullOrBlank()) setRequestProperty("Authorization", "Bearer $token")
        }
        return try {
            if (body != null) connection.outputStream.bufferedWriter().use { it.write(body.toString()) }
            val status = connection.responseCode
            if (status !in 200..299) throw IllegalStateException("Authentication request failed (HTTP $status)")
            val stream = if (status == HttpURLConnection.HTTP_NO_CONTENT) null else connection.inputStream
            if (stream == null) JSONObject() else stream.bufferedReader().use { JSONObject(it.readText()) }
        } finally {
            connection.disconnect()
        }
    }
}
