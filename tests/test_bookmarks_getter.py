from src.handymatt import BookmarksGetter


if __name__ == '__main__':
    
    # get bookmarks
    print('Initializing Getter')
    getter = BookmarksGetter(
        browser='brave',
        profile='Profile 6',
        localappdata=r'C:\Users\stirl\AppData\Local',
    )
    bookmarks = getter.get_bookmarks(
        foldername='MultiDown/4chan',
        sortby='url',
    )
    
    # # 
    print(f'\nGot {len(bookmarks)} bookmarks:')
    for bm in bookmarks:
        print(bm.url)
    print()
