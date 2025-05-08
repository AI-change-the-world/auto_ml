package org.xiaoshuyui.automl.common;

import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serial;
import java.io.Serializable;
import lombok.Data;

@Data
@Schema(name = "接口返回对象", description = "接口返回对象")
public class Result<T> implements Serializable {

  @Serial private static final long serialVersionUID = 1L;

  /** 成功标志 */
  @Schema(name = "success")
  private boolean success = true;

  /** 返回处理消息 */
  @Schema(name = "message")
  private String message = "操作成功！";

  /** 返回代码 */
  @Schema(name = "code")
  private Integer code = 0;

  /** 返回数据对象 data */
  @Schema(name = "data")
  private T data;

  /** 时间戳 */
  @Schema(name = "timestamp")
  private long timestamp = System.currentTimeMillis();

  public Result() {}

  public static <T> Result<T> OK() {
    Result<T> r = new Result<T>();
    r.setSuccess(true);
    r.setCode(CommonConstants.SC_OK_200);
    r.setMessage("成功");
    return r;
  }

  public static <T> Result<T> OK_msg(String msg) {
    Result<T> r = new Result<T>();
    r.setSuccess(true);
    r.setCode(CommonConstants.SC_OK_200);
    r.setMessage(msg);
    return r;
  }

  public static <T> Result<T> OK_data(T data) {
    Result<T> r = new Result<T>();
    r.setSuccess(true);
    r.setCode(CommonConstants.SC_OK_200);
    // r.setResult(data);
    r.setData(data);
    return r;
  }

  public static Result<Object> error(String msg) {
    return error(CommonConstants.SC_INTERNAL_SERVER_ERROR_500, msg);
  }

  public static Result<Object> error(int code, String msg) {
    Result<Object> r = new Result<Object>();
    r.setCode(code);
    r.setMessage(msg);
    r.setSuccess(false);
    return r;
  }
}
