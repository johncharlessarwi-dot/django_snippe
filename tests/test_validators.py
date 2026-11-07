import pytest
from django.core.exceptions import ValidationError

from django_snippe.validators import (
    CurrencyValidator,
    PaymentValidator,
    PayoutValidator,
    PhoneValidator,
    validate_recipient_name,
)


@pytest.mark.parametrize("currency", ["TZS", "KES", "UGX"])
def test_currency_validator_accepts_supported_currencies(currency):
    CurrencyValidator.validate_currency(currency)


def test_currency_validator_rejects_unsupported_currency():
    with pytest.raises(ValidationError):
        CurrencyValidator.validate_currency("USD")


@pytest.mark.parametrize(
    "phone",
    ["0712345678", "255712345678", "+255712345678", "0742345678"],
)
def test_phone_validator_accepts_valid_tanzania_numbers(phone):
    PhoneValidator.validate_phone(phone)


@pytest.mark.parametrize("phone", ["", "123", "07123", "not-a-phone"])
def test_phone_validator_rejects_invalid_numbers(phone):
    with pytest.raises(ValidationError):
        PhoneValidator.validate_phone(phone)


@pytest.mark.parametrize("name", ["a", "", "   "])
def test_validate_recipient_name_rejects_too_short(name):
    with pytest.raises(ValidationError):
        validate_recipient_name(name)


def test_validate_recipient_name_accepts_valid_name():
    validate_recipient_name("Jane Doe")


class TestPaymentValidator:
    def test_valid_mobile_payment(self):
        valid, errors = PaymentValidator.validate_payment_data(
            amount=5000, currency="TZS", phone_number="0712345678", payment_type="mobile"
        )
        assert valid is True
        assert errors == []

    def test_rejects_non_positive_amount(self):
        valid, errors = PaymentValidator.validate_payment_data(
            amount=0, currency="TZS", phone_number="0712345678", payment_type="mobile"
        )
        assert valid is False
        assert any("amount" in e for e in errors)

    def test_rejects_unsupported_currency(self):
        valid, errors = PaymentValidator.validate_payment_data(
            amount=5000, currency="USD", phone_number="0712345678", payment_type="mobile"
        )
        assert valid is False
        assert any("currency" in e for e in errors)

    def test_rejects_invalid_phone_for_mobile(self):
        valid, errors = PaymentValidator.validate_payment_data(
            amount=5000, currency="TZS", phone_number="123", payment_type="mobile"
        )
        assert valid is False
        assert any("phone_number" in e for e in errors)

    def test_card_payment_does_not_require_phone(self):
        valid, errors = PaymentValidator.validate_payment_data(
            amount=5000, currency="TZS", phone_number="", payment_type="card"
        )
        assert valid is True

    def test_rejects_unsupported_payment_type(self):
        valid, errors = PaymentValidator.validate_payment_data(
            amount=5000, currency="TZS", phone_number="0712345678", payment_type="bitcoin"
        )
        assert valid is False


class TestPayoutValidator:
    def test_valid_mobile_payout(self):
        valid, errors = PayoutValidator.validate_payout_data(
            amount=5000,
            currency="TZS",
            channel="mobile",
            recipient_name="Jane Doe",
            recipient_phone="0712345678",
        )
        assert valid is True
        assert errors == []

    def test_requires_recipient_name(self):
        valid, errors = PayoutValidator.validate_payout_data(
            amount=5000, currency="TZS", channel="bank", recipient_name=" "
        )
        assert valid is False
        assert any("recipient_name" in e for e in errors)

    def test_bank_channel_does_not_require_phone(self):
        valid, errors = PayoutValidator.validate_payout_data(
            amount=5000, currency="TZS", channel="bank", recipient_name="Jane Doe"
        )
        assert valid is True

    def test_rejects_unsupported_channel(self):
        valid, errors = PayoutValidator.validate_payout_data(
            amount=5000, currency="TZS", channel="crypto", recipient_name="Jane Doe"
        )
        assert valid is False


def test_regression_18_rejects_boolean_payment_amount():
    valid, _ = PaymentValidator.validate_payment_data(True, 'TZS', '0712345678', 'mobile')
    assert not valid


def test_regression_19_rejects_huge_payment_amount():
    valid, _ = PaymentValidator.validate_payment_data(100_000_001, 'TZS', '0712345678', 'mobile')
    assert not valid


def test_regression_20_accepts_maximum_supported_payment_amount():
    valid, _ = PaymentValidator.validate_payment_data(100_000_000, 'TZS', '0712345678', 'mobile')
    assert valid


def test_regression_21_rejects_boolean_payout_amount():
    valid, _ = PayoutValidator.validate_payout_data(True, 'TZS', 'bank', 'Jane Doe')
    assert not valid


def test_regression_22_rejects_huge_payout_amount():
    valid, _ = PayoutValidator.validate_payout_data(100_000_001, 'TZS', 'bank', 'Jane Doe')
    assert not valid


def test_regression_23_rejects_negative_payout_amount():
    valid, _ = PayoutValidator.validate_payout_data(-1, 'TZS', 'bank', 'Jane Doe')
    assert not valid


def test_regression_24_rejects_punctuation_phone_injection():
    with pytest.raises(ValidationError):
        PhoneValidator.validate_phone('0712345678<script>')


def test_regression_25_rejects_extra_digits_in_phone_number():
    with pytest.raises(ValidationError):
        PhoneValidator.validate_phone('0712345678999')


def test_regression_26_rejects_mobile_number_with_alphabet_characters():
    with pytest.raises(ValidationError):
        PhoneValidator.validate_phone('071234a678')


def test_regression_27_rejects_phone_number_boolean():
    with pytest.raises(ValidationError):
        PhoneValidator.validate_phone(True)


def test_regression_28_rejects_phone_number_integer():
    with pytest.raises(ValidationError):
        PhoneValidator.validate_phone(712345678)


def test_regression_29_rejects_mobile_landline_prefix():
    with pytest.raises(ValidationError):
        PhoneValidator.validate_phone('0212345678')


def test_regression_30_rejects_international_plus_repetition():
    with pytest.raises(ValidationError):
        PhoneValidator.validate_phone('++255712345678')
