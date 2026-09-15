/**
 * PhonePe Payment Gateway (V2 API) Integration Client
 * Invariants:
 * 1. Uses V2 OAuth Token generation (Client ID + Client Secret), NOT deprecated V1 Salt Keys.
 * 2. Mandatory Idempotent Merchant Order ID.
 * 3. Server-to-Server HMAC SHA256 Webhook Signature Verification.
 * 4. Authoritative server status check before fulfilling goods/services.
 */

import crypto from 'crypto';

export interface PhonePeConfig {
  clientId: string;
  clientSecret: string;
  clientVersion: number;
  environment: 'SANDBOX' | 'PRODUCTION';
  callbackUrl: string;
}

export interface CreateOrderPayload {
  merchantOrderId: string;
  amountInPaise: number; // PhonePe expects integer paise (₹100 = 10000 paise)
  redirectUrl: string;
  mobileNumber?: string;
  message?: string;
}

export class PhonePeGateway {
  private baseUrl: string;

  constructor(private config: PhonePeConfig) {
    this.baseUrl = config.environment === 'PRODUCTION'
      ? 'https://api.phonepe.com/apis/hermes'
      : 'https://api-preprod.phonepe.com/apis/pg-sandbox';
  }

  /**
   * Generates OAuth Authorization Token for V2 API calls
   */
  async getAuthToken(): Promise<string> {
    const response = await fetch(`${this.baseUrl}/v1/oauth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id: this.config.clientId,
        client_secret: this.config.clientSecret,
        client_version: this.config.clientVersion.toString(),
        grant_type: 'client_credentials',
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to authenticate with PhonePe: ${response.statusText}`);
    }

    const data = await response.json();
    return data.access_token;
  }

  /**
   * Initiates payment order via /v2/pay
   */
  async createPaymentOrder(order: CreateOrderPayload): Promise<{ redirectUrl: string; orderId: string }> {
    const token = await this.getAuthToken();
    const payload = {
      merchantOrderId: order.merchantOrderId,
      amount: order.amountInPaise,
      redirectUrl: order.redirectUrl,
      callbackUrl: this.config.callbackUrl,
      paymentFlow: {
        type: 'PG_CHECKOUT',
        message: order.message || 'Payment for Order',
      },
    };

    const response = await fetch(`${this.baseUrl}/v2/pay`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    if (!response.ok || result.state === 'FAILED') {
      throw new Error(`PhonePe order creation failed: ${result.message || 'Unknown error'}`);
    }

    return {
      redirectUrl: result.redirectUrl,
      orderId: result.orderId,
    };
  }

  /**
   * Verifies incoming webhook HMAC SHA256 signature
   */
  verifyWebhookSignature(rawBody: string, receivedSignature: string): boolean {
    const expectedSignature = crypto
      .createHmac('sha256', this.config.clientSecret)
      .update(rawBody)
      .digest('hex');

    return crypto.timingSafeEqual(
      Buffer.from(receivedSignature, 'utf8'),
      Buffer.from(expectedSignature, 'utf8')
    );
  }

  /**
   * Authoritative Order Status Reconciliation: /v2/order/{merchantOrderId}/status
   */
  async checkOrderStatus(merchantOrderId: string): Promise<{ state: 'COMPLETED' | 'FAILED' | 'PENDING'; amount: number }> {
    const token = await this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/v2/order/${merchantOrderId}/status`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    const result = await response.json();
    return {
      state: result.state,
      amount: result.amount,
    };
  }
}
