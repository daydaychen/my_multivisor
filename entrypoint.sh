#!/bin/bash

# 如果运行在测试环境, 添加外网路由
if [[ "${RUN_MODE}" == "test" ]]; then
  route add default gw 10.204.16.243
fi

# 读取用户输入，如果命令参数以`python -m`开始, 则使用supervisord守护启动
_CMD="$*"

if [[ -n "${MULTIVISOR_ADDR}" ]]; then
  # 更新multivisor地址
  sed -i "s/localhost:22000/${MULTIVISOR_ADDR}/g" supervisord/supervisord.conf
  # 避免单多容器组文件冲突
  sed -i "s#/supervisord\.#/supervisord_${RANDOM}\.#g" supervisord/supervisord.conf
  # 启用multivisor
  sed -i "s/;//g" supervisord/supervisord.conf
fi

# 更新supervisord.program配置
if [[ -n "${MODULE_NAME}" ]]; then
  sed -i "s/program:name/program:${MODULE_NAME}/g" supervisord/app.conf
fi

echo "exec ${_CMD}" >>supervisord/app.sh

# 启动supervisord
exec supervisord -c supervisord/supervisord.conf
