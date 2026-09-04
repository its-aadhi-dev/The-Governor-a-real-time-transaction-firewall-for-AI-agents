export class VoiceCommandParser {
    parse(transcript) {
        const text = transcript.trim();

        if (!text) {
            throw new Error("Voice command is empty.");
        }

        const maximumPrice = this.extractMaximumPrice(text);

        if (maximumPrice === null) {
            throw new Error(
                "Could not detect a maximum price. Say something like: buy this for up to 800 rupees."
            );
        }

        return {
            maximumPrice,
            currency: "INR",
            rawTranscript: text,
        };
    }

    extractMaximumPrice(text) {
        const normalized = text
            .toLowerCase()
            .replace(/,/g, "")
            .replace(/₹/g, " rupees ");

        const patterns = [
            /(?:up to|maximum|max|under|below)\s+(?:rs\.?|inr|rupees?)?\s*(\d+(?:\.\d+)?)/i,
            /(?:for|at)\s+(?:rs\.?|inr|rupees?)?\s*(\d+(?:\.\d+)?)/i,
            /(\d+(?:\.\d+)?)\s*(?:rs\.?|inr|rupees?)/i,
        ];

        for (const pattern of patterns) {
            const match = normalized.match(pattern);

            if (match) {
                const value = Number(match[1]);

                if (Number.isFinite(value) && value > 0) {
                    return Number(value.toFixed(2));
                }
            }
        }

        return null;
    }
}
