# 网络状态检测工具 - Android版

这是一个用于检测网络状态的Android应用程序，基于原PyQt版本改编而来。

## 功能特点

- 显示当前IP地址和地理位置
- 检测网络访问状态
- 显示Google访问区域
- 测试GitHub连接速度
- 检测学术机构登录状态

## 技术栈

- Kotlin
- Jetpack Compose
- OkHttp
- Coroutines
- Material Design

## 系统要求

- Android 5.0 (API 21) 或更高版本
- 需要网络访问权限

## 构建说明

1. 确保已安装Android Studio最新版本
2. 克隆此仓库
3. 在Android Studio中打开项目
4. 等待Gradle同步完成
5. 点击"运行"按钮或使用`./gradlew assembleDebug`命令构建

## 使用方法

1. 启动应用
2. 点击"刷新"按钮开始检测
3. 等待检测完成，查看各项指标结果

## 注意事项

- 某些功能可能需要VPN或代理服务器
- 部分检测可能受网络环境影响
- 建议在WiFi环境下使用

## 许可证

MIT License 