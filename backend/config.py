# ===== 讯飞语音识别配置 =====
# 获取步骤：
# 1. 打开 https://console.xfyun.cn/
# 2. 注册/登录 → 创建应用 → 选择"语音听写"服务
# 3. 在应用详情页找到以下三个值，填到引号里

XUNFEI = {
    "app_id": "a77c3da6",        # 应用ID，是一串数字
    "api_key": "6a9d05e78987cc2d29fdc00194921c55",      # APIKey
    "api_secret": "MzAwMDhlYmZmYTZjOTQ0NTFmNzcxYTc4", # APISecret
}

# 讯飞语音听写 API 地址
XUNFEI_ASR_URL = "https://raasr.xfyun.cn/api/short"