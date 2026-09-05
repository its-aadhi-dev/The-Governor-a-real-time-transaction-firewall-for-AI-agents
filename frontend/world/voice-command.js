export class VoiceCommandParser {
    parse(transcript) {
        const text = transcript.trim();

        if (!text) {
            throw new Error(
                "Voice command is empty.",
            );
        }

        const lower = text.toLowerCase();

        if (!/\b(buy|purchase|get|order)\b/.test(lower)) {
            throw new Error(
                "I could not identify a purchase command.",
            );
        }

        const maximumPrice =
            this.extractMaximumPrice(text);

        const itemQuery =
            this.extractItemQuery(text);

        return {
            maximumPrice,
            itemQuery,
            currency: "INR",
            rawTranscript: text,
            needsMaximumPrice:
                maximumPrice === null,
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
            const match =
                normalized.match(pattern);

            if (match) {
                const value = Number(
                    match[1],
                );

                if (
                    Number.isFinite(value) &&
                    value > 0
                ) {
                    return Number(
                        value.toFixed(2),
                    );
                }
            }
        }

        return null;
    }

    extractItemQuery(text) {
        const match = text.match(
            /\b(?:buy|purchase|get|order)\s+(.+?)(?=\s+(?:for|at|up to|under|below|maximum|max)\b|$)/i,
        );

        if (!match) {
            return null;
        }

        const itemQuery = match[1]
            .trim()
            .replace(
                /^(this|that|the)\s+/i,
                "",
            );

        return itemQuery || null;
    }
}


