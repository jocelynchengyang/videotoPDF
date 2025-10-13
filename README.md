# videotoPDF

Dependencies

Requires HomeBrew

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

==> Next steps:
- Run these two commands in your terminal to add Homebrew to your PATH:
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"

  # Install PortAudio
brew install portaudio

# Install ffmpeg (needed for merging audio/video)
brew install ffmpeg

# Now install PyAudio
pip3 install pyaudio
