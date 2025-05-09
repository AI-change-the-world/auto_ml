<div align="center">
  <img src="./readme/icon_with_text.png" width="300" height="300">
</div>

### framework

![image](./readme/image.png)

**Notice:** This project is in the early stages of development. Please do not use it in a production environment.

### requirements

* python3.10+ (AI tools)
* java (backend)
* flutter (frontend)
* ffmpeg (video processing)
* docker (mysql, rnacos, minio)


### BUG list
* [x] **[frontend]** image size not match when browser size changed (maybe not a bug)

### TODO list
* [ ] **[frontend]** i18n translation (P4)
* [ ] **[frontend，backend]** other type datasources save to local s3 (P1)
    * [ ] support zip file upload
* [ ] **[frontend，backend]** save annotation after modify (P1)
    * [x] show dialog if unsaved (p4)
    * [x] save annotation after triggered button (p3)
    * [ ] save annotation automaticly (p1)
* [x] **[frontend，backend]** append new data to existing dataset (P2)
* [ ] **[frontend，backend]** append new data to existing annotation (P4)
* [ ] **[backend]** resize image when image size larger than 1024*1024, otherwise sometimes MLLM detection is bad (P1)
