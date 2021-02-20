# spotifytransfer

This program is designed to transfer Spotify playlists to Amazon Music Unlimited. It makes use of the Spotify API to pull playlist information. Since Amazon Music does not currently have an API, the program uses selenium to automate the manual addition of songs to playlists via the Amazon Music website. 

## TODO:
- [x] Fix timing
- [ ] Optimize timing
- [x] Add constraints for artist / look for right songname - artist combination
- [x] Change how you look for right artist from _in_ to _like_
- [ ] Add second search strategy for songs not found in first round, e.g. combine song name and artist for search term
- [ ] Skip songs already contained in playlist
- [ ] Dynamic selection of playlist
- [ ] Investigate spotify API for universal song identifiers to improve search results
- [ ] Investigate use of machine learning to select the correct search results
- [ ] Investigate use of parallelization
- [ ] Investigate why headless approach is so slow
- [ ] Write web application
- [ ] Publish

## ML brainstorm:
- input for model: playlist
- model makes selections from search results and builds a virtual playlist, i.e. adds selection to a list object
- error is difference between input and virtual playlist 
-> try to improve result selection
