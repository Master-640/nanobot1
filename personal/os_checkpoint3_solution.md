# 操作系统 Checkpoint 3 解决方案：多CPU压力测试

## 问题分析

根据描述，你需要通过多CPU下的压力测试（Checkpoint 3）。这涉及到修改内核代码以适应更高的中断频率和更多线程的并发执行。

## 第一步：按要求修改配置文件

### 1. 修改 `sched.c`
```c
// 找到sched.c中的两条logf语句并注释掉
// 原来可能类似这样：
// logf("sched: switching from %s to %s", old->name, next->name);

// 改为：
// logf("sched: switching from %s to %s", old->name, next->name);  // 注释掉这行
```

### 2. 修改 `timer.h`
```c
// 找到timer.h中的TICKS_PER_SEC定义
// 原来可能类似：
// #define TICKS_PER_SEC 100

// 改为：
#define TICKS_PER_SEC 400  // 提高中断频率到400Hz
```

### 3. 修改 `nommu_init.c`
```c
// 找到nommu_init.c中的NTHREAD和SLEEP_TIME定义
// 原来可能类似：
// #define NTHREAD 4
// #define SLEEP_TIME 100

// 改为：
#define NTHREAD 15      // 增加线程数到15
#define SLEEP_TIME 50   // 减少睡眠时间到50
```

## 第二步：理解多CPU问题的根本原因

根据Checkpoint 2的提示，问题可能出在**CSR（控制状态寄存器）的保存和恢复**上。在多CPU环境下，当发生任务切换时，需要正确保存和恢复CPU状态。

### 关键点：sret指令的正确使用

根据RISC-V特权级手册章节3.3.2：
- `sret`指令用于从Supervisor模式返回到User模式
- 它会从`sstatus`寄存器恢复中断使能位
- 会从`sepc`寄存器恢复程序计数器

### 常见问题及解决方案

#### 问题1：CSR值在sched前后不一致
```c
// 在schedule()函数中，确保正确保存和恢复寄存器
void schedule(void) {
    // 保存当前上下文
    struct context *old = current->context;
    
    // 切换到新进程
    current = next;
    
    // 恢复新进程的上下文
    switch_to(old, next->context);
}
```

#### 问题2：多CPU间的同步问题
```c
// 使用原子操作或自旋锁保护共享数据结构
void acquire_spinlock(spinlock_t *lock) {
    while (__sync_lock_test_and_set(&lock->locked, 1) != 0) {
        // 等待锁释放
    }
}

void release_spinlock(spinlock_t *lock) {
    __sync_lock_release(&lock->locked);
}
```

## 第三步：具体调试步骤

### 1. 检查上下文切换代码
```c
// 在trap.c或类似的异常处理文件中
void trap_handler(void) {
    // 保存所有寄存器
    save_context();
    
    // 处理中断或异常
    if (is_timer_interrupt()) {
        timer_interrupt_handler();
    }
    
    // 可能需要调度
    if (should_schedule()) {
        schedule();
    }
    
    // 恢复上下文
    restore_context();
}
```

### 2. 确保正确的sret使用
```c
// 从内核模式返回用户模式时
void return_to_user(uint64_t epc, uint64_t status) {
    // 设置sepc和sstatus
    write_csr(sepc, epc);
    write_csr(sstatus, status);
    
    // 执行sret
    asm volatile("sret");
}
```

### 3. 添加调试信息
```c
// 在关键位置添加有限的调试输出
void debug_sched(const char *msg) {
    static int count = 0;
    if (count++ < 100) {  // 只输出前100次，避免过多输出
        logf("[DEBUG] CPU%d: %s", cpuid(), msg);
    }
}
```

## 第四步：预期输出和验证

成功通过测试后，你应该看到：
```
1 [INFO 1,1] init: init ends!
2 [PANIC 1,1] os/proc.c:218: init process exited
3 [PANIC 2,-1] os/trap.c:45: other CPU has panicked
4 [PANIC 0,-1] os/trap.c:45: other CPU has panicked
5 [PANIC 3,-1] os/trap.c:45: other CPU has panicked
```

这表示：
1. init进程正常结束
2. 其他CPU检测到panic并正确传播panic信息

## 第五步：常见问题排查

### 如果遇到死锁：
1. 检查自旋锁实现是否正确
2. 确保没有中断处理程序中获取锁
3. 使用死锁检测工具或添加超时机制

### 如果遇到数据竞争：
1. 为每个CPU使用独立的运行队列
2. 确保对共享数据的访问有锁保护
3. 使用内存屏障指令确保内存一致性

### 如果遇到计时器问题：
```c
// 确保每个CPU有独立的计时器上下文
struct per_cpu_timer {
    uint64_t ticks;
    uint64_t next_tick;
};

// 在timer_interrupt_handler中处理CPU特定的计时器
void timer_interrupt_handler(void) {
    int cpu = cpuid();
    per_cpu_timer[cpu].ticks++;
    
    // 检查是否需要调度
    if (per_cpu_timer[cpu].ticks >= per_cpu_timer[cpu].next_tick) {
        schedule();
    }
}
```

## 第六步：测试脚本

创建一个自动化测试脚本：
```bash
#!/bin/bash
# test_smp.sh
PASS_COUNT=0
FAIL_COUNT=0
MAX_TESTS=15

echo "开始多CPU压力测试..."
for i in $(seq 1 $MAX_TESTS); do
    echo "测试 $i/$MAX_TESTS..."
    
    # 运行测试，捕获输出
    OUTPUT=$(make runsmp 2>&1)
    
    # 检查是否出现预期panic
    if echo "$OUTPUT" | grep -q "init process exited" && \
       echo "$OUTPUT" | grep -q "other CPU has panicked"; then
        echo "✓ 测试 $i 通过"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "✗ 测试 $i 失败"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        echo "输出:"
        echo "$OUTPUT" | tail -20
    fi
    
    # 如果连续失败太多，提前停止
    if [ $FAIL_COUNT -ge 3 ]; then
        echo "连续失败次数过多，停止测试"
        break
    fi
done

echo "测试完成: 通过 $PASS_COUNT, 失败 $FAIL_COUNT"
if [ $PASS_COUNT -ge 10 ]; then
    echo "✅ Checkpoint 3 通过！"
else
    echo "❌ Checkpoint 3 未通过"
fi
```

## 总结

关键修改点：
1. **减少日志输出**以避免性能影响
2. **提高中断频率**以增加压力测试强度
3. **增加线程数**以测试并发能力
4. **修复CSR保存/恢复问题**确保多CPU正确运行
5. **正确处理sret指令**避免特权级切换问题

如果按照上述步骤修改后仍然有问题，可能需要：
1. 使用GDB进行单步调试
2. 添加更详细的调试信息（但仅在问题复现时开启）
3. 检查内存分配和释放是否正确
4. 验证每个CPU的栈空间是否足够

记住，多CPU调试的核心在于**状态一致性**和**同步正确性**。祝你好运！