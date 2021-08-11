# 代码地址：

[https://github.com/Sharpiless/yolov5-knowledge-distillation](https://github.com/Sharpiless/yolov5-knowledge-distillation)

<img width="800" src="https://user-images.githubusercontent.com/26833433/98699617-a1595a00-2377-11eb-8145-fc674eb9b1a7.jpg"></a>

# 教师模型：

```bash
python train.py --weights weights/yolov5m.pt \
        --cfg models/yolov5m.yaml --data data/voc.yaml --epochs 50 \
        --batch-size 8 --device 0 --hyp data/hyp.scratch.yaml 
```

# 蒸馏训练：

```bash
python train.py --weights weights/yolov5s.pt \
        --cfg models/yolov5s.yaml --data data/voc.yaml --epochs 50 \
        --batch-size 8 --device 0 --hyp data/hyp.scratch.yaml \
        --t_weights yolov5m.pt --distill
```

# 训练参数:

> --weights：预训练模型

> --t_weights：教师模型权重

> --distill：使用知识蒸馏进行训练

> --dist_loss：l2或者kl

> --temperature：使用知识蒸馏时的温度


使用[《Object detection at 200 Frames Per Second》](https://arxiv.org/pdf/1805.06361.pdf)中的损失

这篇文章分别对这几个损失函数做出改进，具体思路为只有当teacher network的objectness value高时，才学习bounding box坐标和class probabilities。

![](https://github.com/Sharpiless/Yolov5-distillation-train-inference/blob/main/data/images/full_loss.png)

![](https://github.com/Sharpiless/Yolov5-distillation-train-inference/blob/main/data/images/all.png)


# 实验结果：


这里假设VOC2012中新增加的数据为无标签数据（2k张）。

|教师模型|训练方法|蒸馏损失|P|R|mAP50|
|:----|:----|:----|:----|:----|:----|
|无|正常训练|不使用|0.7756|0.7115|0.7609|
|Yolov5l|output based|l2|0.7585|0.7198|0.7644|
|Yolov5l|output based|KL|0.7417|0.7207|0.7536|
|Yolov5m|output based|l2|0.7682|0.7436|0.7976|
|Yolov5m|output based|KL|0.7731|0.7313|0.7931|

![训练结果](https://github.com/Sharpiless/yolov5-distillation-5.0/blob/main/images/line.png)

参数和细节正在完善，支持KL散度、L2 logits损失和Sigmoid蒸馏损失等

## 1. 正常训练：

![正常训练](https://github.com/Sharpiless/yolov5-distillation-5.0/blob/main/images/%E6%AD%A3%E5%B8%B8%E8%AE%AD%E7%BB%83.png)

## 2. L2蒸馏损失：

![L2蒸馏损失](https://github.com/Sharpiless/yolov5-distillation-5.0/blob/main/images/l+l2.png)

# 我的公众号：

![在这里插入图片描述](https://img-blog.csdnimg.cn/20210310070958646.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80NDkzNjg4OQ==,size_16,color_FFFFFF,t_70)

# 关于作者
> B站：[https://space.bilibili.com/470550823](https://space.bilibili.com/470550823)

> CSDN：[https://blog.csdn.net/weixin_44936889](https://blog.csdn.net/weixin_44936889)

> AI Studio：[https://aistudio.baidu.com/aistudio/personalcenter/thirdview/67156](https://aistudio.baidu.com/aistudio/personalcenter/thirdview/67156)

> Github：[https://github.com/Sharpiless](https://github.com/Sharpiless)
