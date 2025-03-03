package com.networkstatus.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class MainActivity : ComponentActivity() {
    private val client = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(5, TimeUnit.SECONDS)
        .build()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                NetworkStatusScreen(
                    onRefresh = { refreshNetworkStatus() }
                )
            }
        }
    }

    @Composable
    fun NetworkStatusScreen(onRefresh: () -> Unit) {
        var ipInfo by remember { mutableStateOf<Map<String, String>?>(null) }
        var networkStatus by remember { mutableStateOf("检查中...") }
        var googleRegion by remember { mutableStateOf("检查中...") }
        var githubSpeed by remember { mutableStateOf("检查中...") }
        var academicName by remember { mutableStateOf("检查中...") }
        var isLoading by remember { mutableStateOf(false) }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                text = "网络状态检测工具",
                style = MaterialTheme.typography.h5,
                modifier = Modifier.align(Alignment.CenterHorizontally)
            )

            if (isLoading) {
                LinearProgressIndicator(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(4.dp)
                )
            }

            Card(
                modifier = Modifier.fillMaxWidth(),
                elevation = 4.dp
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(text = "IP信息：${ipInfo?.get("ip") ?: "获取中..."}")
                    Text(text = "位置：${ipInfo?.get("region") ?: ""}")
                }
            }

            Card(
                modifier = Modifier.fillMaxWidth(),
                elevation = 4.dp
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(text = "网络访问状态：$networkStatus")
                    Text(text = "Google地区：$googleRegion")
                    Text(text = "GitHub连接速度：$githubSpeed")
                    Text(text = "学术机构：$academicName")
                }
            }

            Button(
                onClick = {
                    isLoading = true
                    onRefresh()
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp)
            ) {
                Text("刷新")
            }
        }
    }

    private fun refreshNetworkStatus() {
        lifecycleScope.launch {
            try {
                // 获取IP信息
                val ipResponse = client.newCall(
                    Request.Builder()
                        .url("http://ip-api.com/json")
                        .build()
                ).execute()
                
                val ipJson = JSONObject(ipResponse.body?.string() ?: "{}")
                
                // 检查网络自由度
                val urls = listOf(
                    "https://www.youtube.com/generate_204",
                    "https://www.google.com/generate_204",
                    "https://github.com"
                )
                
                var successCount = 0
                for (url in urls) {
                    try {
                        val response = client.newCall(
                            Request.Builder()
                                .url(url)
                                .build()
                        ).execute()
                        if (response.code in 200..299) {
                            successCount++
                        }
                    } catch (e: Exception) {
                        // 忽略连接错误
                    }
                }
                
                // 更新UI
                setContent {
                    MaterialTheme {
                        NetworkStatusScreen(
                            onRefresh = { refreshNetworkStatus() }
                        )
                    }
                }
                
            } catch (e: Exception) {
                // 处理错误
            }
        }
    }
} 