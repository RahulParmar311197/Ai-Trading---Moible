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
        var selectedTab by remember { mutableIntStateOf(0) }
        Column(Modifier.fillMaxSize()) {
            Text("AI Trading", style = MaterialTheme.typography.headlineMedium, modifier = Modifier.padding(24.dp))
            TabRow(selectedTabIndex = selectedTab) {
                listOf("Home", "AI", "Paper").forEachIndexed { index, title ->
                    Tab(selected = selectedTab == index, onClick = { selectedTab = index }, text = { Text(title) })
                }
            }
            when (selectedTab) {
                0 -> HomeScreen()
                1 -> AiScreen()
                2 -> PaperScreen()
            }
        }
    }
}

@Composable
private fun HomeScreen() {
    Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Analyze → Replay → Backtest → Paper Trade → Live Trade")
        Text("Live trading is explicitly gated. This Android client has no live-order path.")
        Text("Use Paper to inspect the deterministic paper portfolio.")
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
private fun PaperScreen() {
    var status by remember { mutableStateOf("Paper portfolio not loaded.") }
    var loading by remember { mutableStateOf(false) }
    val executor = remember { Executors.newSingleThreadExecutor() }
    Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Paper Portfolio", style = MaterialTheme.typography.titleLarge)
        Text("Paper mode only. No broker credentials are used.")
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(enabled = !loading, onClick = {
                loading = true
                executor.execute {
                    val result = try {
                        val account = PaperApiClient(BuildConfig.AI_API_BASE_URL).account()
                        "Balance ${account.balance} · Equity ${account.equity} · Positions ${account.positions} · Halted ${account.tradingHalted}"
                    } catch (error: Exception) { "Paper portfolio unavailable: ${error.message ?: "request failed"}" }
                    androidx.compose.runtime.snapshots.Snapshot.withMutableSnapshot { status = result; loading = false }
                }
            }) { Text(if (loading) "Loading…" else "Refresh") }
        }
        Text(status)
    }
}
