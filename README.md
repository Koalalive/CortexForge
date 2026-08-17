# MRI Brain → 3D Print

从脑部 MRI 生成可用于 3D 打印的大脑皮层 STL 模型的完整流程。

```
DICOM ──dcm2niix──▶ NIfTI ──FreeSurfer recon-all──▶ pial 表面 ──▶ STL ──▶ 合并+水密+平滑
```

## 做了什么

- **DICOM → NIfTI**：`dcm2niix` 转换 3D T1 结构像，校正方向为 RAS
- **皮层重建**：FreeSurfer `recon-all -all`（Docker 内后台跑，CPU 4~8 小时）
- **表面提取**：`mris_convert` 把左右半球 pial 表面转成 STL
- **合并 + 水密**：`trimesh` 合并左右半球，输出可直接切片的 `brain_full.stl`
- **平滑**：Taubin 平滑（保体积、保沟回），输出 `brain_full_smooth.stl`

## 输出示例规格

- 水密闭合网格（左右半球各一个壳）
- 尺寸 ≈ 147 × 173 × 122 mm（真实成人脑大小，打印时可缩放）
- 脑体积 ≈ 1227 cm³

## 完整教程

见 [SKILL.md](SKILL.md)。

## 依赖

- Docker + 含 FreeSurfer 的镜像
- FreeSurfer License（免费注册获取，**请勿上传 license**）
- Python：`pydicom`、`dcm2niix`、`trimesh`、`nibabel`

## 隐私提醒

MRI 数据、患者信息、FreeSurfer license 均属敏感内容，本仓库仅含流程教程与脚本，**不含任何数据文件**。
