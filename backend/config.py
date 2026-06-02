# ===== 讯飞语音识别配置 =====
# 获取步骤：
# 1. 打开 https://console.xfyun.cn/
# 2. 注册/登录 → 创建应用 → 选择"语音听写"服务
# 3. 在应用详情页找到以下三个值，填到引号里

XUNFEI = {
    "app_id": "a77c3da6",
    "api_key": "6a9d05e78987cc2d29fdc00194921c55",
    "api_secret": "MzAwMDhlYmZmYTZjOTQ0NTFmNzcxYTc4",
}

# 讯飞语音听写 v1 REST API（短音频，≤60秒）
# 文档：https://www.xfyun.cn/doc/asr/voicedictation/API.html
XUNFEI_ASR_URL = "http://api.xfyun.cn/v1/service/v1/iat"


# ===== DeepSeek 大模型配置（语义解析）=====
# 获取步骤：
# 1. 打开 https://platform.deepseek.com/
# 2. 注册/登录 → API Keys → 创建新的 API Key
# 3. 把 key 填到下面的引号里
# 4. 新用户通常有免费额度（约500万 tokens）

DEEPSEEK = {
    "api_key": "你的DeepSeek-API-Key",   # 格式: sk-xxxxxxxxxxxxxxxx
    "model": "deepseek-chat",            # 模型名称（deepseek-chat 便宜够用）
}

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
