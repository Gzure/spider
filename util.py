# -*- coding:UTF-8 -*-
import six


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
    import commands
    text = commands.getoutput('ipconfig'.encode('gb2312'))
    print text.decode('gb2312')