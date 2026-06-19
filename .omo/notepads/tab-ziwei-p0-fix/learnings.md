# Learnings — Tab + 紫微流年 P0 修复

## Tab 渲染策略改为 CSS 隐藏

### 问题
分析页 7 个 Tab 使用条件渲染，导致切换 Tab 时整棵子树被销毁重建。

### 解决方案
改为始终渲染，用 CSS display:none 控制可见性。

## 紫微流年 cancelled 守卫

### 解决方案
添加 zwFetchCancelledRef + cleanup useEffect + Promise.all .then 中检查。
