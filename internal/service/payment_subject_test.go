package service

import (
	"testing"

	"github.com/dujiao-next/internal/constants"
	"github.com/dujiao-next/internal/models"
)

func TestBuildPaymentSubjectAlipayUsesAntiFraudOrderNo(t *testing.T) {
	order := &models.Order{
		OrderNo: "DJ202606050001",
		Items: []models.OrderItem{
			{TitleJSON: models.JSON{constants.LocaleZhCN: "测试商品"}},
		},
	}

	got := buildPaymentSubject(order, constants.PaymentProviderOfficial, constants.PaymentChannelTypeAlipay)
	want := "他人截图让你扫码均是诈骗，订单号：DJ202606050001"
	if got != want {
		t.Fatalf("subject = %q, want %q", got, want)
	}
}

func TestBuildPaymentSubjectNonAlipayKeepsOrderSubject(t *testing.T) {
	order := &models.Order{
		OrderNo: "DJ202606050002",
		Items: []models.OrderItem{
			{TitleJSON: models.JSON{constants.LocaleZhCN: "测试商品"}},
		},
	}

	got := buildPaymentSubject(order, constants.PaymentProviderOfficial, constants.PaymentChannelTypeWechat)
	want := "测试商品"
	if got != want {
		t.Fatalf("subject = %q, want %q", got, want)
	}
}
