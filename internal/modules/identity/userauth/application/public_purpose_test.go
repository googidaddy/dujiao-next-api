package application

import (
	"context"
	"errors"
	"testing"

	"github.com/dujiao-next/internal/constants"
)

// 2026-11-16：扫描器用公开发码接口向任意邮箱发 Telegram 绑定 / 改绑邮箱验证码。
// 这里锁定边界：公开入口只允许注册与重置密码。
func TestSendVerifyCodeRejectsNonPublicPurposes(t *testing.T) {
	svc := &Service{}
	for _, purpose := range []string{
		constants.VerifyPurposeTelegramBind,
		constants.VerifyPurposeChangeEmailOld,
		constants.VerifyPurposeChangeEmailNew,
		"unknown",
	} {
		err := svc.SendVerifyCode(context.Background(), "someone@example.com", purpose, "zh-CN", "")
		if !errors.Is(err, ErrInvalidVerifyPurpose) {
			t.Fatalf("purpose %q: want ErrInvalidVerifyPurpose, got %v", purpose, err)
		}
	}
}

func TestPublicVerifyPurposeAllowsRegisterAndReset(t *testing.T) {
	for _, purpose := range []string{constants.VerifyPurposeRegister, constants.VerifyPurposeReset} {
		if !isPublicVerifyPurpose(purpose) {
			t.Fatalf("purpose %q should be allowed", purpose)
		}
	}
}
