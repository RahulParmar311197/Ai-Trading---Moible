package com.aitrading.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
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

@androidx.compose.runtime.Composable
private fun AppRoot() {
    MaterialTheme {
        var symbol by remember { mutableStateOf("NIFTY") }
        var timeframe by remember { mutableStateOf("15m") }
        var summary by remember { mutableStateOf("AI analysis is advisory only and does not execute trades.") }
        var loading by remember { mutableStateOf(false) }
        val executor = remember { Executors.newSingleThreadExecutor() }

        Column(
            modifier = Modifier.fillMaxSize().padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("AI Trading", style = MaterialTheme.typography.headlineMedium)
            Text("Advisory AI analysis")
            OutlinedTextField(
                value = symbol,
                onValueChange = { symbol = it },
                label = { Text("Symbol") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            OutlinedTextField(
                value = timeframe,
                onValueChange = { timeframe = it },
                label = { Text("Timeframe") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Button(
                enabled = !loading,
                onClick = {
                    loading = true
                    executor.execute {
                        val result = try {
                            AiApiClient(BuildConfig.AI_API_BASE_URL).analyze(symbol, timeframe)
                        } catch (error: Exception) {
                            "AI analysis unavailable: ${error.message ?: "request failed"}"
                        }
                        androidx.compose.runtime.snapshots.Snapshot.withMutableSnapshot {
                            summary = result
                            loading = false
                        }
                    }
                },
            ) { Text(if (loading) "Analyzing…" else "Analyze") }
            Text(summary)
        }
    }
}
