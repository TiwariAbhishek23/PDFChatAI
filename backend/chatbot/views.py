import fitz  # PyMuPDF
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Document
from .serializers import DocumentSerializer
from .utils import extract_text_from_pdf, get_embedding, chunk_text, find_relevant_documents, generate_augmented_response


class DocumentUploadViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        title = request.data.get('title', file.name)

        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        # Extract text from PDF
        extracted_text = extract_text_from_pdf(file)

        # Split text into chunks and generate embeddings
        text_chunks = chunk_text(extracted_text)
        embeddings = [get_embedding(chunk) for chunk in text_chunks]

        # Store the first chunk's embedding (you can refine this logic)
        document = Document.objects.create(
            title=title,
            file=file,
            extracted_text=extracted_text,
            embedding=embeddings[0] if embeddings else None
        )
        serializer = DocumentSerializer(document)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class QueryView(APIView):
    def post(self, request):
        user_query = request.data.get("query")

        if not user_query:
            return Response({"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate query embedding
        query_embedding = get_embedding(user_query)

        # Retrieve similar documents
        retrieved_docs = find_relevant_documents(query_embedding)

        # Generate response with augmentation
        if retrieved_docs and retrieved_docs[0]["similarity"] > 0.5:  # Threshold check
            response_text = generate_augmented_response(user_query, retrieved_docs)
        else:
            response_text = f"I couldn't find relevant documents, but here's my best answer: {generate_augmented_response(user_query, [])}"

        return Response({"response": response_text}, status=status.HTTP_200_OK)
