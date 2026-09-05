export class RazorpayCheckout {
	constructor() {
		this.instance = null;
	}

	async open({
		keyId,
		orderId,
		amount,
		currency,
		itemName,
		transactionId,
	}) {
		if (!window.Razorpay) {
			throw new Error(
				"Razorpay Checkout script is unavailable.",
			);
		}

		if (!keyId) {
			throw new Error(
				"Razorpay public key is missing.",
			);
		}

		if (!orderId) {
			throw new Error(
				"Razorpay order ID is missing.",
			);
		}

		if (!transactionId) {
			throw new Error(
				"Transaction ID is missing.",
			);
		}

		const options = {
			key: keyId,

			amount: String(
				Math.round(
					Number(amount) * 100,
				),
			),

			currency,

			name: "The Governor",

			description:
				itemName ||
				"Governed AI transaction",

			order_id: orderId,

			notes: {
				transaction_id: transactionId,
			},

			handler: async (response) => {
				console.log(
					"[Razorpay Success]",
					response,
				);

				try {
					const result =
						await this.verifyPayment(
							transactionId,
							response,
						);

					console.log(
						"[Governor Payment Verified]",
						result,
					);

					window.dispatchEvent(
						new CustomEvent(
							"governor-payment-verified",
							{
								detail: result,
							},
						),
					);
				} catch (error) {
					console.error(
						"[Governor Payment Verification Failed]",
						error,
					);

					window.dispatchEvent(
						new CustomEvent(
							"governor-payment-verification-failed",
							{
								detail: {
									error:
										error.message,
								},
							},
						),
					);
				}
			},

			modal: {
				ondismiss: () => {
					console.log(
						"[Razorpay] Checkout dismissed.",
					);

					window.dispatchEvent(
						new CustomEvent(
							"governor-payment-dismissed",
						),
					);
				},
			},
		};

		this.instance =
			new window.Razorpay(options);

		this.instance.on(
			"payment.failed",
			(response) => {
				console.error(
					"[Razorpay Payment Failed]",
					response,
				);

				window.dispatchEvent(
					new CustomEvent(
						"governor-payment-failed",
						{
							detail:
								response,
						},
					),
				);
			},
		);

		this.instance.open();
	}

	async verifyPayment(
		transactionId,
		response,
	) {
		const requiredFields = [
			"razorpay_payment_id",
			"razorpay_order_id",
			"razorpay_signature",
		];

		for (const field of requiredFields) {
			if (!response?.[field]) {
				throw new Error(
					`Razorpay response is missing ${field}.`,
				);
			}
		}

		const result = await fetch(
			`/api/v1/transactions/${encodeURIComponent(
				transactionId,
			)}/verify-payment`,
			{
				method: "POST",

				headers: {
					"Content-Type":
						"application/json",
				},

				body: JSON.stringify({
					razorpay_payment_id:
						response.razorpay_payment_id,

					razorpay_order_id:
						response.razorpay_order_id,

					razorpay_signature:
						response.razorpay_signature,
				}),
			},
		);

		const data = await result.json();

		if (!result.ok) {
			throw new Error(
				data.detail ||
				`Payment verification failed (${result.status}).`,
			);
		}

		return data;
	}
}

