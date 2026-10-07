@echo off
chcp 65001 >nul
set HX=D:\software\HBuilderX.5.26.2026091802
set PROJ=D:\git-double\bahar\baharUniapp

echo ==========================================================
echo   会员端 H5 本地启动（uni-app / HBuilderX 5.26）
echo ==========================================================
echo.
echo [前置] 后端需先启动（零售 8081）：
echo        在项目根执行  deploy\start-all.sh
echo        或在 IDEA 里跑 BaharApplication
echo.
echo [1/3] 打开 HBuilderX 并加载会员端项目...
start "" "%HX%\HBuilderX.exe" "%PROJ%"
echo        首次启动较慢，等待 25 秒...
timeout /t 25 /nobreak >nul

echo [2/3] 触发「运行到浏览器」（H5）...
"%HX%\cli.exe" run --platform h5 --project baharUniapp

echo.
echo [3/3] 就绪后访问：
echo         http://localhost:8080/h5/
echo.
echo ----------------------------------------------------------
echo   登录：账号填「会员姓名」（如 张伟 / 王芳 / 李娜）
echo         密码 123456，图形验证码见输入框旁图片
echo   切换行业：地址后加 ?m=car / ?m=food / ?m=health
echo             （也可只改 config.js 上层，或走后端 8082/8083/8084）
echo   后端端口：零售 8081 / 汽车美容 8082 / 餐饮 8083 / 康养美业 8084
echo ----------------------------------------------------------
echo.
echo   若上一行提示「未检测到已打开的HBuilderX」，
echo   说明 HBuilderX 还没启动完，请在它界面里手动点：
echo       运行 -^> 运行到浏览器 -^> Chrome
echo.
pause
