# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""SuperBench devices module."""

from superbench.common.devices.gpu import GPU

__all__ = [
    'GPU',
]
#__all__ 的主要作用是明确指定当使用 from package import * 时，应该导入哪些子模块、类、函数或变量。如果没有定义 __all__，则默认会导入所有不以下划线 _ 开头的名称（即非私有成员）。
