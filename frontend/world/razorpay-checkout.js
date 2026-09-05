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

		const options = {
			key: keyId,
			amount: String(
				Math.round(Number(amount) * 100),
			),
			currency,
			name: "The Governor",
			description:
				itemName || "Governed AI transaction",
			order_id: orderId,
			notes: {
				transaction_id: transactionId,
			},
			handler: (response) => {
				console.log(
					"[Razorpay Success]",
					response,
				);

				window.dispatchEvent(
					new CustomEvent(
						"governor-payment-success",
						{
							detail: response,
						},
					),
				);
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

		this.instance = new window.Razorpay(options);

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
							detail: response,
						},
					),
				);
			},
		);

		this.instance.open();
	}
}
