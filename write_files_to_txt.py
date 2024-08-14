import os
import tiktoken

# Initialize the tokenizer
encoding = tiktoken.get_encoding("cl100k_base")  # or use "gpt-4"

def count_tokens(text):
    """Return the number of tokens in the given text."""
    return len(encoding.encode(text))

def split_files_by_tokens(root_dir, max_tokens_per_file):
    chunk_number = 1
    current_tokens = 0
    current_chunk = []

    def write_chunk():
        nonlocal chunk_number, current_chunk, current_tokens
        if current_chunk:
            output_filename = f"chunk_{chunk_number}.txt"
            with open(output_filename, 'w', encoding='utf-8') as outfile:
                outfile.write("\n".join(current_chunk))
            print(f"Written {output_filename} with {current_tokens} tokens")
            chunk_number += 1
            current_chunk = []
            current_tokens = 0

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip __pycache__ directories
        if '__pycache__' in dirnames:
            dirnames.remove('__pycache__')
        
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as infile:
                content = infile.read()

            # Count tokens in the content
            tokens = count_tokens(content)
            
            # Check if adding this file exceeds the max token limit
            if current_tokens + tokens + count_tokens(f"\n--- File: {file_path} ---\n") > max_tokens_per_file:
                write_chunk()  # Write the current chunk and start a new one

            # Add file path and content to the current chunk
            current_chunk.append(f"--- File: {file_path} ---")
            current_chunk.append(content)
            current_tokens += tokens + count_tokens(f"\n--- File: {file_path} ---\n")

    # Write any remaining content as the last chunk
    write_chunk()

if __name__ == "__main__":
    # Set the root directory and maximum tokens per file
    root_directory = "autollama"  # The directory containing your project files
    max_tokens = 4000  # Maximum tokens per chunk

    # Call the function to split files by tokens
    split_files_by_tokens(root_directory, max_tokens)
