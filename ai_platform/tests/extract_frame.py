def extract_keyframes(video_path, interval_sec=2.0):
    import os
    import cv2
    import ffmpeg

    probe = ffmpeg.probe(video_path, select_streams="v")
    duration = float(probe["streams"][0]["duration"])
    cap = cv2.VideoCapture(video_path)
    current_time = 0.0
    frame_idx = 0

    # 使用外部传入路径，否则使用默认目录
    save_directory = "./keyframes"
    os.makedirs(save_directory, exist_ok=True)

    while current_time < duration:
        cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
        ret, frame = cap.read()
        if not ret:
            break

        save_name = f"frame_{frame_idx:04d}.png"
        save_path = os.path.join(save_directory, save_name)
        cv2.imwrite(save_path, frame)

        frame_idx += 1
        current_time += interval_sec  # 每隔 interval 秒取一帧

    cap.release()

extract_keyframes("./test.mp4")