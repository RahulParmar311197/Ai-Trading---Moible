package com.aitrading.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import java.util.concurrent.Executors

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { AppRoot() }
    }
}

@Composable
private fun AppRoot() {
    MaterialTheme {
        val context = LocalContext.current
        val tokenStore = remember { AuthTokenStore(context.applicationContext) }
        var token by remember { mutableStateOf(tokenStore.read()) }
        if (token.isNullOrBlank()) {
            LoginScreen(onAuthenticated = { accessToken ->
                tokenStore.write(accessToken)
                token = accessToken
            })
        } else {
            AuthenticatedApp(token = token!!, onLogout = {
                tokenStore.clear()
                token = null
            })
        }
    }
}

@Composable
private fun LoginScreen(onAuthenticated: (String) -> Unit) {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("Sign in to access your paper portfolio.") }
    var loading by remember { mutableStateOf(false) }
    val executor = remember { Executors.newSingleThreadExecutor() }
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("AI Trading", style = MaterialTheme.typography.headlineMedium)
        Text("Secure session required. Live trading remains explicitly gated.")
        OutlinedTextField(email, { email = it }, label = { Text("Email") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        OutlinedTextField(
            password,
            { password = it },
            label = { Text("Password") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            visualTransformation = PasswordVisualTransformation(),
        )
        Button(enabled = !loading && email.isNotBlank() && password.isNotBlank(), onClick = {
            loading = true
            executor.execute {
                try {
                    val result = AuthApiClient(BuildConfig.AI_API_BASE_URL).login(email.trim(), password)
                    androidx.compose.runtime.snapshots.Snapshot.withMutableSnapshot {
                        loading = false
                        onAuthenticated(result.token)
                    }
                } catch (error: Exception) {
                    androidx.compose.runtime.snapshots.Snapshot.withMutableSnapshot {
                        loading = false
                        status = "Sign-in unavailable: ${error.message ?: "request failed"}"
                    }
                }
            }
        }) { Text(if (loading) "Signing in…" else "Sign in") }
        Text(status)
    }
}

@Composable
private fun AuthenticatedApp(token: String, onLogout: () -> Unit) {
    var selectedTab by remember { mutableIntStateOf(0) }
    Column(Modifier.fillMaxSize()) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text("AI Trading", style = MaterialTheme.typography.headlineMedium)
            Button(onClick = onLogout) { Text("Sign out") }
        }
        TabRow(selectedTabIndex = selectedTab) {
            listOf("Home", "AI", "Paper").forEachIndexed { index, title ->
                Tab(selected = selectedTab == index, onClick = { selectedTab = index }, text = { Text(title) })
            }
        }
        when (selectedTab) {
            0 -> HomeScreen()
            1 -> AiScreen()
            2 -> PaperScreen(token)
        }
    }
}

@Composable
private fun HomeScreen() {
    Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Analyze → Replay → Backtest → Paper Trade → Live Trade")
        Text("Live trading is explicitly gated. This Android client has no live-order path.")
        Text("Your paper session is authenticated and isolated by application user.")
    }
}

@Composable
private fun AiScreen() {
    var symbol by remember { mutableStateOf("NIFTY") }
    var timeframe by remember { mutableStateOf("15m") }
    var summary by remember { mutableStateOf("AI analysis is advisory only and does not execute trades.") }
    var loading by remember { mutableStateOf(false) }
    val executor = remember { Executors.newSingleThreadExecutor() }
    Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Advisory AI analysis")
        OutlinedTextField(symbol, { symbol = it }, label = { Text("Symbol") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        OutlinedTextField(timeframe, { timeframe = it }, label = { Text("Timeframe") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        Button(enabled = !loading, onClick = {
            loading = true
            executor.execute {
                val result = try { AiApiClient(BuildConfig.AI_API_BASE_URL).analyze(symbol, timeframe) }
                catch (error: Exception) { "AI analysis unavailable: ${error.message ?: "request failed"}" }
                androidx.compose.runtime.snapshots.Snapshot.withMutableSnapshot { summary = result; loading = false }
            }
        }) { Text(if (loading) "Analyzing…" else "Analyze") }
        Text(summary)
    }
}

@Composable
private fun PaperScreen(token: String) {
    var status by remember { mutableStateOf("Paper portfolio not loaded.") }
    var loading by remember { mutableStateOf(false) }
    val executor = remember { Executors.newSingleThreadExecutor() }
    Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Paper Portfolio", style = MaterialTheme.typography.titleLarge)
        Text("Authenticated paper mode only. Broker credentials remain server-side.")
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(enabled = !loading, onClick = {
                loading = true
                executor.execute {
                    val result = try {
                        val account = PaperApiClient(BuildConfig.AI_API_BASE_URL, token).account()
                        "Balance ${account.balance} · Equity ${account.equity} · Positions ${account.positions} · Halted ${account.tradingHalted}"
                    } catch (error: Exception) { "Paper portfolio unavailable: ${error.message ?: "request failed"}" }
                    androidx.compose.runtime.snapshots.Snapshot.withMutableSnapshot { status = result; loading = false }
                }
            }) { Text(if (loading) "Loading…" else "Refresh") }
        }
        Text(status)
    }
}
