import axios, { AxiosError } from 'axios';
import { message } from 'antd';

export type ApiErrorPayload = {
  success?: boolean;
  code?: number;
  error_code?: string | null;
  message?: string | null;
  detail?: unknown;
  data?: unknown;
  timestamp?: string;
};

export class ApiClientError extends Error {
  code?: number;
  errorCode?: string | null;
  detail?: unknown;
  httpStatus?: number;
  payload?: ApiErrorPayload;

  constructor(params: {
    message: string;
    code?: number;
    errorCode?: string | null;
    detail?: unknown;
    httpStatus?: number;
    payload?: ApiErrorPayload;
  }) {
    super(params.message);
    this.name = 'ApiClientError';
    this.code = params.code;
    this.errorCode = params.errorCode;
    this.detail = params.detail;
    this.httpStatus = params.httpStatus;
    this.payload = params.payload;
  }
}

type ApiErrorActionHandler = (error: ApiClientError) => void;

const actionHandlers = new Set<ApiErrorActionHandler>();

export const registerApiErrorHandler = (handler: ApiErrorActionHandler) => {
  actionHandlers.add(handler);
  return () => {
    actionHandlers.delete(handler);
  };
};

const isApiErrorPayload = (value: unknown): value is ApiErrorPayload => {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const maybe = value as Record<string, unknown>;
  return (
    typeof maybe.message === 'string'
    || typeof maybe.code === 'number'
    || typeof maybe.error_code === 'string'
    || 'detail' in maybe
  );
};

export const toApiClientError = (error: unknown, fallback = '请求失败'): ApiClientError => {
  if (error instanceof ApiClientError) {
    return error;
  }

  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorPayload>;
    const payload = isApiErrorPayload(axiosError.response?.data)
      ? axiosError.response?.data
      : undefined;
    const detail = payload?.detail;
    const message = (
      (typeof detail === 'string' && detail)
      || payload?.message
      || axiosError.message
      || fallback
    );
    return new ApiClientError({
      message,
      code: payload?.code,
      errorCode: payload?.error_code ?? null,
      detail,
      httpStatus: axiosError.response?.status,
      payload,
    });
  }

  if (error instanceof Error) {
    return new ApiClientError({ message: error.message || fallback });
  }

  return new ApiClientError({ message: fallback });
};

export const extractApiErrorMessage = (error: unknown, fallback = '请求失败') => {
  return toApiClientError(error, fallback).message;
};

export const resolveApiErrorPresentation = (
  error: unknown,
  fallback = '请求失败',
): {
  text: string;
  level: 'warning' | 'error';
  error: ApiClientError;
} => {
  const normalized = toApiClientError(error, fallback);

  if (normalized.errorCode === 'CAPABILITY_UNAVAILABLE') {
    return {
      text: normalized.message || fallback,
      level: 'warning',
      error: normalized,
    };
  }

  if (
    normalized.code === 401
    || normalized.errorCode === 'UNAUTHORIZED'
    || normalized.code === 403
    || normalized.errorCode === 'FORBIDDEN'
  ) {
    return {
      text: normalized.message || fallback,
      level: 'warning',
      error: normalized,
    };
  }

  return {
    text: normalized.message || fallback,
    level: 'error',
    error: normalized,
  };
};

export const showApiError = (error: unknown, fallback = '请求失败') => {
  const presentation = resolveApiErrorPresentation(error, fallback);
  actionHandlers.forEach((handler) => {
    try {
      handler(presentation.error);
    } catch (handlerError) {
      console.error('[API Error Handler Failed]', handlerError);
    }
  });
  if (presentation.level === 'warning') {
    message.warning(presentation.text);
  } else {
    message.error(presentation.text);
  }
  return presentation.error;
};
