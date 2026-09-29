package com.bahar.module.backendApi.controller.common;

import com.bahar.common.service.CaptchaService;
import com.bahar.common.util.SeqUtil;
import com.bahar.framework.web.BaseController;
import com.bahar.framework.web.ResponseObject;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.AllArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

/**
 * 后台登录图形验证码（可读 uuid 版本）
 *
 * 说明：
 *   原 /backendApi/captcha/getCode 在服务端随机生成 uuid 并写入 Redis，
 *   但并未把 uuid 返回给调用方，而 /backendApi/login/doLogin 校验时必须使用同一个 uuid，
 *   因此任何自行实现的管理端都无法完成登录。
 *   本控制器为纯增量补充：生成 uuid 后连同图片一起返回，不改动原有任何逻辑。
 *
 *   路径置于 /backendApi/captcha/** 之下，属于 WebConfig 中已放行的鉴权白名单。
 *
 * Created by WorkBuddy
 * CopyRight https://www.bahar.cn
 */
@Api(tags = "管理端-登录验证码接口")
@RestController
@AllArgsConstructor
@RequestMapping("/backendApi/captcha")
public class BackendLoginCaptchaController extends BaseController {

    /**
     * 图形验证码生成器服务
     */
    private CaptchaService captchaService;

    /**
     * 获取登录验证码（同时返回 uuid 与 base64 图片）
     */
    @ApiOperation(value = "获取登录图形验证码")
    @GetMapping("/getLoginCode")
    public ResponseObject getLoginCode() throws Exception {
        String uuid = SeqUtil.getUUID();
        BufferedImage codeImage = captchaService.getCodeByUuid(uuid);

        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        ImageIO.write(codeImage, "jpg", outputStream);
        String base64Image = Base64.getEncoder().encodeToString(outputStream.toByteArray());

        Map<String, Object> result = new HashMap<>();
        result.put("uuid", uuid);
        result.put("image", "data:image/jpeg;base64," + base64Image);
        return getSuccessResult(result);
    }
}
