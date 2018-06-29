
if __name__ == '__main__':

    args = parser.parse_args()

    if os.path.isdir(args.dirOutput):
        fmt = 'the output directory "{}" already exists, overwrite? (y/n)? '
        while True:
            answer = raw_input(fmt.format(args.dirOutput)).strip().lower()
            if answer == "n":
                sys.stderr.write("exiting...")
                sys.exit()
            elif answer == "y":
                break
    else:
        os.makedirs(args.dirOutput)

    log.startLogging(sys.stdout)

    q = Queue.Queue()
    lines = [line.rstrip('\n') for line in open(args.fileInput)]
    fileNumber = 0
    for fileName in lines:
        print(fileName)
        q.put((fileNumber, fileName))
        fileNumber += 1

    hostname = "stream.watsonplatform.net"
    headers = {'X-WDC-PL-OPT-OUT': '1'} if args.optOut else {}

    if args.tokenauth:
        headers['X-Watson-Authorization-Token'] = (
            Utils.getAuthenticationToken('https://' + hostname,
                                         'speech-to-text',
                                         args.credentials[0],
                                         args.credentials[1]))
    else:
        auth = args.credentials[0] + ":" + args.credentials[1]
        headers["Authorization"] = "Basic " + base64.b64encode(auth)

    print(headers)
    fmt = "wss://{}/speech-to-text/api/v1/recognize?model={}"
    url = fmt.format(hostname, args.model)
    if args.am_custom_id != None:
        url += "&acoustic_customization_id=" + args.am_custom_id
    if args.lm_custom_id != None:
        url += "&customization_id=" + args.lm_custom_id
    print url
    summary = {}
    factory = WSInterfaceFactory(q, summary, args.dirOutput, args.contentType,
                                 args.model, url, headers, debug=False)
    factory.protocol = WSInterfaceProtocol

    for i in range(min(int(args.threads), q.qsize())):

        factory.prepareUtterance()

        if factory.isSecure:
            contextFactory = ssl.ClientContextFactory()
        else:
            contextFactory = None
        connectWS(factory, contextFactory)

    reactor.run()

    fileHypotheses = args.dirOutput + "/hypotheses.txt"
    f = open(fileHypotheses, "w")
    successful = 0
    emptyHypotheses = 0
    print sorted(summary.items())
    counter = 0
    for key, value in enumerate(sorted(summary.items())):
        value = value[1]  
        if value['status']['code'] == 1000:
            print('{}: {} {}'.format(key, value['status']['code'],
                                     value['hypothesis'].encode('utf-8')))
            successful += 1
            if value['hypothesis'][0] == "":
                emptyHypotheses += 1
        else:
            fmt = '{}: {status[code]} REASON: {status[reason]}'
            print(fmt.format(key, **status))
        f.write('{}: {}\n'.format(counter + 1, value['hypothesis'].encode('utf-8')))
        counter += 1
    f.close()
    fmt = "successful sessions: {} ({} errors) ({} empty hypotheses)"
    print(fmt.format(successful, len(summary) - successful, emptyHypotheses))