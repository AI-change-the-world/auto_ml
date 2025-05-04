package org.xiaoshuyui.automl.common;

import lombok.Data;

@Data
public class PythonApiResponse<T> {
    public int status;
    public String message;
    public T data;
}
