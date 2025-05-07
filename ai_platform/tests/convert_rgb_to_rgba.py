from PIL import Image

# 打开图片并转换为 RGBA 模式（支持 alpha 通道）
img = Image.open(
    "/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/cut_img.png"
).convert("RGBA")

datas = img.getdata()
new_data = []

# 设置一个阈值，避免因压缩或抗锯齿导致白色不纯
threshold = 240

for item in datas:
    # item 是一个 (R, G, B, A) 元组
    r, g, b, a = item
    if r > threshold and g > threshold and b > threshold:
        # 将接近白色的像素设为透明
        new_data.append((255, 255, 255, 0))
    else:
        new_data.append((r, g, b, a))

# 应用修改并保存
img.putdata(new_data)
img.save("output.png", "PNG")
