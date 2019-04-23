# -*- coding:UTF-8 -*-
import six


def import_module(ref):
    if not isinstance(ref, six.string_types):
        raise TypeError('References must be strings')
    if ':' not in ref:
        raise ValueError('Invalid reference')

    modulename, rest = ref.split(':', 1)
    try:
        obj = __import__(modulename, fromlist=[rest])
    except ImportError:
        raise LookupError('Error resolving reference %s: could not import module' % modulename)

    return obj


def ref_to_obj(ref):
    """
    Returns the object pointed to by ``ref``.

    :type ref: str

    """
    if not isinstance(ref, six.string_types):
        raise TypeError('References must be strings')
    if ':' not in ref:
        raise ValueError('Invalid reference')

    modulename, rest = ref.split(':', 1)
    try:
        obj = __import__(modulename, fromlist=[rest])
    except ImportError:
        raise LookupError('Error resolving reference %s: could not import module' % ref)

    try:
        for name in rest.split('.'):
            obj = getattr(obj, name)
        return obj
    except Exception:
        raise LookupError('Error resolving reference %s: error looking up object' % ref)


if __name__ == '__main__':
    # import commands
    # text = commands.getoutput('ipconfig'.encode('gb2312'))
    # print text.decode('gb2312')
    import re
    import codecs
    reg = re.compile('^[\d]{4}-[\d]{2}-[\d]{2}')
    f = codecs.open('spider.log', 'rb', 'utf-8')
    # f = open('spider.log', 'rb')
    lines = f.readline(size=500)
    print len(lines)
    print lines
    f.close()
    # res = []
    # for line in lines:
    #     if reg.match(line):
    #         line_array = line.strip().split(' ', 4)
    #         line_info = {
    #             'time': line_array[0] + ' ' + line_array[1],
    #             'level': line_array[2],
    #             'module': line_array[3],
    #             'message': line_array[4]
    #         }
    #         res.append(line_info)