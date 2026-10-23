# Docomo结构适配与专项验证

来源、公式对应和差异见[最终口径](当前实验口径与推进顺序.md)。保留每AP本地DFT波束、QPSK共相位及AP逻辑DFT模式，采用三轮交替坐标更新。三轮和逻辑AP顺序是项目选择，不称为作者代码复现。

专项48项检查通过，9个随机案例、6个物理案例，所有观测目标更新不下降、比特解码重放误差0。三个B=4固定本地波束案例各枚举256种候选，当前结果与枚举最优一致；此验证不涵盖本地波束联合全局搜索。

- [专项结果](../results/docomo_validation/docomo_audit.json)
- [每轮目标与枚举差距](../results/docomo_validation/docomo_objective_checks.csv)
- [论文来源哈希和对应关系](../results/docomo_validation/paper_correspondence.json)
- [单流正式结果](UPA单流400位置正式实验报告.md)
- [双流统一扩展结果](UPA单极化双流扩展验证报告.md)

论文的二维规则AP、多极化和OFDM未在当前实验中复现；论文Type-I NCJT也不同于项目的含共相位Type-I。反馈按实际消息计数，默认单流129 bit，统一双流扩展157 bit，不能采用论文表II的26 bit或据此宣称十分之一开销。
