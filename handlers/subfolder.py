import logging
from utils.common import BaseHandler, ProcessingContext
from utils.matchers import normalize_text
from utils.model_utils import get_model

class SubfolderHandler(BaseHandler):
    def handle(self, context: ProcessingContext) -> None:
        """
        Uses a machine learning model to classify the document text into a target subfolder.
        Updates the context with the predicted subfolder path and the classification confidence.
        """
        model = get_model()
        if not model or not context.text:
            return

        norm_text = normalize_text(context.text)
        probs = model.predict_proba([norm_text])[0]
        
        # Log top 3 categories
        top_indices = probs.argsort()[-3:][::-1]
        for idx in top_indices:
            logging.info(f"  Possible Category: {model.classes_[idx]} ({probs[idx]:.2f})")

        best_idx = probs.argmax()
        context.confidence = probs[best_idx]
        context.subfolder = model.classes_[best_idx]
        
        logging.info(f"  ML Classification: '{context.subfolder}' with confidence {context.confidence:.2f}")