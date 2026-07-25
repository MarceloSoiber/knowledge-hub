import { HttpErrorResponse } from "@angular/common/http";

export type ApiErrorKind =
  | "network"
  | "validation"
  | "unauthorized"
  | "forbidden"
  | "not-found"
  | "conflict"
  | "too-large"
  | "rate-limited"
  | "provider"
  | "unavailable"
  | "unknown";

export interface ApiError {
  kind: ApiErrorKind;
  status: number;
  message: string;
}

const messages: Record<number, [ApiErrorKind, string]> = {
  400: ["validation", "Confira os dados informados e tente novamente."],
  401: ["unauthorized", "Sua sessão expirou. Informe o token novamente."],
  403: ["forbidden", "Você não tem permissão para concluir esta ação."],
  404: ["not-found", "O recurso solicitado não foi encontrado."],
  409: ["conflict", "Já existe um registro conflitante ou o item está em uso."],
  413: ["too-large", "O arquivo enviado é maior do que o permitido."],
  429: ["rate-limited", "Muitas solicitações em sequência. Aguarde e tente novamente."],
  502: ["provider", "Um serviço de processamento não respondeu corretamente."],
  503: ["unavailable", "O serviço está indisponível no momento. Tente novamente."],
};

export function toApiError(error: HttpErrorResponse): ApiError {
  if (error.status === 0) {
    return { kind: "network", status: 0, message: "Não foi possível conectar à API. Confira a conexão." };
  }

  const mapped = messages[error.status];
  if (mapped) {
    return { kind: mapped[0], status: error.status, message: mapped[1] };
  }

  return { kind: "unknown", status: error.status, message: "Ocorreu um erro inesperado. Tente novamente." };
}
