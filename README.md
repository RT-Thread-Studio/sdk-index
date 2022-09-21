# sdk-index
[![Build Status](https://travis-ci.com/RT-Thread-Studio/sdk-index.svg?branch=master)](https://travis-ci.com/RT-Thread-Studio/sdk-index)

功能检测：

- SDK 管理器索引同步；
- BSP 生成，导入，编译检测；
- CSP 生成，导入，编译检测；
- json 语法检测。

## 注意

1. 提交RT-Thread Studio BSP之前，请先确保提交的内容已经在[RT-Thread主仓库的BSP](https://github.com/RT-Thread/rt-thread/tree/master/bsp)中提交过。请不要在主仓库BSP没有提交/更新的情况下，直接更新RT-Thread Studio的BSP。即RT-Thread Studio BSP不能超前于RT-Thread主仓库BSP，任何bug或者源码更新应当先在主仓库中完成，然后再更新RT-Thread Studio BSP (可以通过 `scons --dist-ide` 一键生成RT-Thread Studio BSP)。

2. 提交RT-Thread Studio BSP前，请确认该BSP在RT-Thread主仓库BSP中可以正确执行 `scons --dist-ide --project-name=xxx --project-path=xxx` 命令。该命令用于直接导出一份RT-Thread Studio BSP工程。[参见PR](https://github.com/RT-Thread/rt-thread/pull/4245)
